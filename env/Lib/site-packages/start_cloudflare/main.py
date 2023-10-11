from enum import Enum
from typing import Final

from pydantic import EmailStr, Field
from pydantic_settings import BaseSettings
from pydantic_settings.main import SettingsConfigDict

CF_API_URL: Final = "https://api.cloudflare.com"
MIME_TYPE: dict[str, str] = {"Content-Type": "application/json"}


class CFSecurityKey(Enum):
    EMAIL = "X-Auth-Email"
    API = "X-Auth-Key"
    USER_SERVICE = "X-Auth-User-Service-Key"
    BEARER = "Authorization"

    def as_header(self, value: str) -> dict[str, str]:
        """Helper to create request headers based on the key.

        Examples:
            >>> CFSecurityKey.BEARER.as_header('Adria-Ripoli')
            {'Authorization': 'Bearer Adria-Ripoli'}

        Args:
            value (str): Value to include in the header

        Returns:
            dict[str, str]: A dictionary that can be combined later to form part of the request URL header
        """  # noqa: E501
        if self.name == "BEARER":
            return {"Authorization": f"Bearer {value}"}
        return {self.value: value}


class CF(BaseSettings):
    """
    This is a base class. Bare minimum: `CF_ACCT_ID` needs to be set.

    Add secrets to .env file:

    Field in .env | Cloudflare API Credential | Where credential found
    :--|:--:|:--
    `CF_ACCT_ID`, defaults to 'ACCT' | Signup Account ID | Assigned on signup `https://dash.cloudflare.com/<ACCT_ID>/`
    Optional: `CF_ACCT_EMAIL` | Account Email | What you signed up with
    Optional: `CF_GLOBAL_API_KEY` | See [docs](https://developers.cloudflare.com/fundamentals/api/get-started/keys/) | `https://dash.cloudflare.com/profile/api-tokens`
    Optional: `CF_ORIGIN_CA_KEY` | See [docs](https://developers.cloudflare.com/fundamentals/api/get-started/ca-keys/) | `https://dash.cloudflare.com/profile/api-tokens`

    Examples:
        >>> import os
        >>> cf = CF()
        >>> cf
        CF(version=4, email=None)
        >>> cf.account_id
        'ACCT'
        >>> from start_cloudflare import CF
        >>> os.environ['CF_ACCT_ID'] = "<ACCT_ID> from https://dash.cloudflare.com/<ACCT_ID>/"
        >>> cf = CF()
        >>> cf
        CF(version=4, email=None)
        >>> cf.account_id
        '<ACCT_ID> from https://dash.cloudflare.com/<ACCT_ID>/'
        >>> CF_API_URL
        'https://api.cloudflare.com'

    """  # noqa: E501

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")  # type: ignore # noqa: E501
    account_id: str | None = Field(
        default="ACCT",
        repr=False,
        validation_alias="CF_ACCT_ID",
    )
    version: int = Field(
        default=4,
        repr=True,
        validation_alias="CF_API_VERSION",
    )
    email: EmailStr | None = Field(
        default=None,
        repr=True,
        validation_alias="CF_ACCT_EMAIL",
    )
    global_api_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias="CF_GLOBAL_API_KEY",
    )
    origin_ca_key: str | None = Field(
        default=None,
        repr=False,
        validation_alias="CF_ORIGIN_CA_KEY",
    )

    @property
    def head_email(self) -> dict[str, str]:
        """Get partial header involving 'X-Auth-Email' key, provided the
        'CF_ACCT_EMAIL' is set.

        Examples:
            >>> import os
            >>> os.environ['CF_ACCT_EMAIL'] = 'brightness@long.ago'
            >>> cf = CF()
            >>> cf.head_email
            {'X-Auth-Email': 'brightness@long.ago'}

        Returns:
            dict[str, str]: Partial header
        """
        if self.email:
            return CFSecurityKey.EMAIL.as_header(self.email)
        raise Exception("Need to set email.")

    @property
    def head_auth_key(self) -> dict:
        """Get partial header involving the 'X-Auth-Email' key, provided the
        'X-Auth-Key' is set.

        Examples:
            >>> import os
            >>> os.environ['CF_GLOBAL_API_KEY'] = 'mytoken'
            >>> cf = CF()
            >>> cf.head_auth_key
            {'X-Auth-Key': 'mytoken'}

        Returns:
            dict[str, str]: Partial header
        """
        if self.global_api_key:
            return CFSecurityKey.API.as_header(self.global_api_key)
        raise Exception("Need to set global api key.")

    @classmethod
    def set_bearer_auth(cls, token: str) -> dict:
        """Get partial header involving the 'Authorization' key, provided the
        'X-Auth-Key' is set.

        Examples:
            >>> CF.set_bearer_auth('Guidanio-Cerra')
            {'Authorization': 'Bearer Guidanio-Cerra'}

        Returns:
            dict[str, str]: Partial header
        """
        return CFSecurityKey.BEARER.as_header(token)

    @property
    def base(self) -> str:
        """Create the base url for the Cloudflare API with version 4 as default

        Examples:
            >>> cf = CF()
            >>> cf.base
            'https://api.cloudflare.com/client/v4'
            >>> import os
            >>> os.environ['CF_API_VERSION'] = '5'
            >>> cf = CF()
            >>> cf.base
            'https://api.cloudflare.com/client/v5'

        Returns:
            str: Partial URL
        """

        return f"{CF_API_URL}/client/v{self.version}"

    def add_account_endpoint(self, path: str) -> str:
        """Set url endpoint following the API reference /accounts/{path}

        Examples:
            >>> cf = CF()
            >>> cf.add_account_endpoint("/test/hello/world")
            'https://api.cloudflare.com/client/v4/accounts/test/hello/world'

        Args:
            path (str): Needs to start with "/"

        Returns:
            str: URL involving "accounts" to fetch endpoint terminating in `path`
        """

        if not path.startswith("/"):
            raise Exception("Path string should start with /")
        return f"{self.base}/accounts{path}"
