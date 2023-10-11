from collections.abc import Iterator
from pathlib import Path

import boto3
from pydantic import Field
from start_cloudflare import CF


class CloudflareR2(CF):
    """
    Add secrets to .env file:

    Field in .env | Cloudflare API Credential | Where credential found
    :--|:--:|:--
    `CF_ACCT_ID` | Account ID | `https://dash.cloudflare.com/<acct_id>/r2`
    `CF_R2_REGION` | Default Region: `apac` | See [options](https://developers.cloudflare.com/r2/learning/data-location/#available-hints)
    `R2_ACCESS_KEY_ID` | Key | When R2 Token created in `https://dash.cloudflare.com/<acct_id>/r2/overview/api-tokens`
    `R2_SECRET_ACCESS_KEY` | Secret | When R2 Token created in `https://dash.cloudflare.com/<acct_id>/r2/overview/api-tokens`

    Examples:
        >>> import os
        >>> os.environ['CF_ACCT_ID'] = "ACT"
        >>> os.environ['R2_ACCESS_KEY_ID'] = "ABC"
        >>> os.environ['R2_SECRET_ACCESS_KEY'] = "XYZ"
        >>> r2 = CloudflareR2()
        >>> type(r2.resource)
        <class 'boto3.resources.factory.s3.ServiceResource'>

    """  # noqa: E501

    region: str = Field(default="apac", repr=True, validation_alias="CF_R2_REGION")
    access_key_id: str = Field(
        default="ABC", repr=False, validation_alias="R2_ACCESS_KEY_ID"
    )  # noqa: E501
    secret_access_key: str = Field(
        default="XYZ", repr=False, validation_alias="R2_SECRET_ACCESS_KEY"
    )

    @property
    def endpoint_url(self):
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    @property
    def resource(self):
        """Access to buckets via instance, e.g. `r2.resource.Bucket('<name>')`"""
        return boto3.resource(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region,
        )

    def get_bucket(self, bucket_name: str):
        """Get an R2 bucket instance."""
        return self.resource.Bucket(bucket_name)  # type: ignore


class CloudflareR2Bucket(CloudflareR2):
    """
    Helper function that can be assigned to each bucket.

    Note [AWS API reference](https://docs.aws.amazon.com/AmazonS3/latest/API) vs. [R2](https://developers.cloudflare.com/r2/data-access/s3-api/api/)

    Examples:
        >>> import os
        >>> os.environ['CF_ACCT_ID'] = "ACT"
        >>> os.environ['R2_ACCESS_KEY_ID'] = "ABC"
        >>> os.environ['R2_SECRET_ACCESS_KEY'] = "XYZ"
        >>> obj = CloudflareR2Bucket(name='test')
        >>> type(obj.bucket)
        <class 'boto3.resources.factory.s3.Bucket'>
    """  # noqa: E501

    name: str

    @property
    def bucket(self):
        return self.get_bucket(self.name)

    @property
    def client(self):
        return self.bucket.meta.client

    def get(self, key: str, *args, **kwargs) -> dict | None:
        """Assumes the key prefix exists in the bucket. See helper
        for [boto3 get_object](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/get_object.html)

        Args:
            key (str): Should exist in the bucket.

        Returns:
            dict | None: Returns `None` if not found.
        """  # noqa: E501
        try:
            return self.client.get_object(Bucket=self.name, Key=key, *args, **kwargs)
        except Exception:
            return None

    def put(self, key: str, *args, **kwargs) -> dict | None:
        """Assumes the key prefix exists in the bucket. See helper
        for [boto3 put_object](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/put_object.html)

        Args:
            key (str): Should exist in the bucket.

        Returns:
            dict | None: Returns `None` if not found.
        """  # noqa: E501
        try:
            return self.client.put_object(Bucket=self.name, Key=key, *args, **kwargs)
        except Exception:
            return None

    def fetch(self, *args, **kwargs) -> dict:
        """Each bucket contain content prefixes but can only be fetched by batches. Each batch is limited
        to a max of 1000 prefixes. Without arguments included in this call, will default to the first 1000 keys.

        See details in [boto3 list-objects-v2 API docs](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/list_objects_v2.html#list-objects-v2)
        """  # noqa: E501
        return self.client.list_objects_v2(Bucket=self.name, *args, **kwargs)

    def all_items(self) -> list[dict] | None:
        """Using pagination conventions from s3 and r2, get all prefixes found in
        the bucket name. Note this aggregates all `fetch()` calls, specifically limiting
        the response to the "Contents" key of each `fetch()` call. Such key will
        contain a list of dict-based prefixes.

        Returns:
            list[dict] | None: Get objects form the bucket
        """
        contents = []
        counter = 1
        next_token = None
        while True:
            print(f"Accessing page {counter=}")
            if counter == 1:
                res = self.fetch()
            elif next_token:
                res = self.fetch(ContinuationToken=next_token)
            else:
                print("Missing next token.")
                break

            next_token = res.get("NextContinuationToken")
            if res.get("Contents"):
                contents.extend(res["Contents"])
            counter += 1
            if not res["IsTruncated"]:  # is False if all results returned.
                print("All results returned.")
                return contents

    @classmethod
    def filter_content(
        cls, filter_suffix: str, objects_list: list[dict]
    ) -> Iterator[dict]:
        """Filter objects based on a `filter_suffix` from either:

        1. List of objects from `self.all_items()`; or
        2. _Contents_ key of `self.fetch()`. Note that each _Contents_ field of `fetch`
        is a dict object, each object will contain a _Key_ field.

        Args:
            filter_suffix (str): Prefix terminates with what suffix
            objects_list (list[dict]): List of objects previously fetched

        Yields:
            Iterator[dict]: Filtered `objects_list` based on `filter_suffix`
        """
        for prefixed_obj in objects_list:
            if key := prefixed_obj.get("Key"):
                if key.endswith(filter_suffix):
                    yield prefixed_obj

    def upload(self, file_like: str | Path, key: str, *args, **kwargs):
        """[Upload](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/client/upload_fileobj.html) local `file_like` contents to r2-bucket path `key`.

        Args:
            file_like (str | Path): Local file
            key (str): Remote location

                Defaults to {}.
        """  # noqa: E501
        with open(file_like, "rb") as read_file:
            return self.bucket.upload_fileobj(read_file, key, *args, **kwargs)

    def download(self, key: str, local_file: str):
        """With a r2-bucket `key`, [download](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3/bucket/download_fileobj.html#download-fileobj) its contents to `local_file`.

        Args:
            key (str): Origin file to download
            local_file (str): Where to download, how to name downloaded file
        """  # noqa: E501
        with open(local_file, "wb") as write_file:
            return self.bucket.download_fileobj(key, write_file)

    def get_root_prefixes(self):
        """See adapted recipe from boto3 re: top-level [prefixes](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/s3.html#list-top-level-common-prefixes-in-amazon-s3-bucket).

        Returns:
            list[str]: Matching prefixes in the root of the bucket.
        """  # noqa: E501
        _objs = []
        paginator = self.client.get_paginator("list_objects")
        result = paginator.paginate(Bucket=self.name, Delimiter="/")
        for prefix in result.search("CommonPrefixes"):
            _objs.append(prefix.get("Prefix"))  # type: ignore
        return _objs
