from datetime import datetime
import json
import openai
from dotenv import load_dotenv
import os
import boto3
import requests

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

session = boto3.Session(
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
)

API_KEY = "12cc955471e5731aadcb000bd6a79ee1"
voice = "en-US-Alex"


async def generate_metadata(prompt):
    messages = [
        {
            "role": "system",
            "content": """THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
You are a metadata generator that will receive a string and generate NOTHING but a dictionary.
The dictionary should have the following fields: title, title_audio_url, toc_audio_url, table_of_contents, end_of_url.
The title field should be the title of the text prompt.
The title_audio_url field should be a text of the title.
The toc_audio_url field should be a text going through the table of contents.
The table_of_contents field should be a list of strings, each string should be a subtopic of the text prompt.
The end_of_url field should be an an text for ending the video.
The format to be followed is {"title":<title string>, "title_audio_url":<title audio url string>, "toc_audio_url":<toc audio url string>, "table_of_contents":[<string>,<string>...], "end_of_url":<end of url string>}. The input string is """,
        },
        {"role": "user", "content": prompt},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
    )

    metadata = response["choices"][0]["message"]["content"]
    print(metadata)

    # Convert string to a dictionary
    metadata = json.loads(metadata)
    # Handle the case where the role field is not `system` or `user`.
    metadata["toc_audio_url"] = await get_audioForMetaData(metadata["toc_audio_url"])
    metadata["title_audio_url"] = await get_audioForMetaData(
        metadata["title_audio_url"]
    )
    metadata["end_of_url"] = await get_audioForMetaData(metadata["end_of_url"])

    return metadata


async def get_audioForMetaData(text_prompt):
    # Upload the text to AWS Polly and get the audio file URL
    print("Audio currently generating", text_prompt)
    response = requests.post(
        "https://api.elevenlabs.io/tts/synthesize",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"text": text_prompt, "voice": voice},
    )
    # Generate a unique object key
    url = requests.put(
        "https://worker-silent-night-fcb9.dhravya.workers.dev/",
        headers={
            "X-Custom-Auth-Key": "yourmom",
            "Content-Type": "audio/mpeg",
        },
        data=response.content,
    )
    return url.content.decode("utf-8")
