import os
import boto3
import asyncio
from datetime import datetime
from aiohttp import ClientSession

AWS_DEFAULT_REGION = "your-aws-region"
REMOTION_AWS_ACCESS_KEY_ID = "your-access-key-id"
REMOTION_AWS_SECRET_ACCESS_KEY = "your-secret-access-key"
AWS_SESSION_TOKEN = "your-session-token"
BUCKET_NAME = "edcomposer"

session = boto3.Session(
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=REMOTION_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=REMOTION_AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

polly = session.client("polly", region_name=AWS_DEFAULT_REGION)

async def getAudio(textPrompt, session):
    # Upload the text to AWS Polly and get the audio file url
    response = polly.synthesize_speech(VoiceId='Joanna', OutputFormat='mp3', Text=textPrompt)
    file_path = "response.mp3"
    async with session.get(response['AudioStream'].url) as response:
        response.raise_for_status()
        audio_data = await response.read()
    
    # Generate a unique object key
    object_key = f"{datetime.timestamp(datetime.now())}-{textPrompt}.mp3"

    # Upload the audio data to S3
    s3 = session.client("s3", region_name=AWS_DEFAULT_REGION)
    try:
        s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=audio_data)
        
        # Generate the download URL for the uploaded file
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_key}"
        
        return s3_url

    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

async def process_batch(text_prompts):
    async with ClientSession() as session:
        tasks = [getAudio(prompt, session) for prompt in text_prompts]
        audio_urls = await asyncio.gather(*tasks)
        return audio_urls

# Example usage:
text_prompts = [
    "Prompt 1",
    "Prompt 2",
    # Add more prompts here
]

loop = asyncio.get_event_loop()
audio_urls = loop.run_until_complete(process_batch(text_prompts))

for i, url in enumerate(audio_urls):
    if url:
        print(f"Audio URL for Prompt {i + 1}: {url}")
