import os
import boto3
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
REMOTION_AWS_ACCESS_KEY_ID = os.getenv("REMOTION_AWS_ACCESS_KEY_ID")
REMOTION_AWS_SECRET_ACCESS_KEY = os.getenv("REMOTION_AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

session = boto3.Session(
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=REMOTION_AWS_ACCESS_KEY_ID,
    aws_secret_access_key=REMOTION_AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)

polly = session.client("polly", region_name=AWS_DEFAULT_REGION)
s3 = boto3.client("s3", region_name=AWS_DEFAULT_REGION,
                  aws_access_key_id=REMOTION_AWS_ACCESS_KEY_ID,
                  aws_secret_access_key=REMOTION_AWS_SECRET_ACCESS_KEY,
                  aws_session_token=AWS_SESSION_TOKEN)

async def get_audio(text_prompt):
    # Upload the text to AWS Polly and get the audio file url
    response = polly.synthesize_speech(VoiceId='Joanna', OutputFormat='mp3', Text=text_prompt)
    
    # Generate a unique object key
    object_key = f"{datetime.timestamp(datetime.now())}-{text_prompt}.mp3"

    # Save the audio from the response
    file_path = f"audio/{object_key}"

    with open(file_path, "wb") as file:
        file.write(response["AudioStream"].read())

    try:
        s3.upload_file(file_path, "edcomposer", object_key)
        
        # Generate the download URL for the uploaded file
        s3_url = f"https://edcomposer.s3.amazonaws.com/{object_key}"

        # Delete the file from the local directory
        os.remove(file_path)
        
        return s3_url

    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

async def process_batch(text_prompts):
    tasks = [get_audio(prompt) for prompt in text_prompts]
    audio_urls = await asyncio.gather(*tasks)
    return audio_urls

# Example usage:
text_prompts = [
    "The Estates-General convened in 1789, leading to the formation of the National Assembly, representing the common people's interests.",
    "The National Constituent Assembly (1789-1791) drafted the Constitution of 1791, establishing a constitutional monarchy.",
    # Add more text prompts here
]

loop = asyncio.get_event_loop()
audio_urls = loop.run_until_complete(process_batch(text_prompts))

for i, url in enumerate(audio_urls):
    if url:
        print(f"Audio URL for Prompt {i + 1}: {url}")
