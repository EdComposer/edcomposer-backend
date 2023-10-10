import os
import boto3
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import aiofiles

# Load the environment variables
load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

boto3.setup_default_session(profile_name='dhanush')
session = boto3.Session( 
)

polly = session.client("polly", region_name=AWS_DEFAULT_REGION)
s3 = boto3.client(
    "s3",
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN,
)


async def get_audio(text_prompt):
    # Upload the text to AWS Polly and get the audio file url
    print("Audio currently generating", text_prompt)
    response = polly.synthesize_speech(
        VoiceId="Joanna", OutputFormat="mp3", Text=text_prompt
    )

    # Generate a unique object key
    object_key = f"{datetime.timestamp(datetime.now())}.mp3"

    # Save the audio from the response
    file_path = f"audio/{object_key}"

    async with aiofiles.open(file_path, "wb") as file:
        await file.write(response["AudioStream"].read())

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


async def process_batch(text_prompts: list[list[str]]):
    # from a list of lists, generate a single list of audio urls
    all_prompts = []

    for prompt_list in text_prompts:
        all_prompts += prompt_list

    tasks = [get_audio(prompt) for prompt in all_prompts]
    audio_urls = await asyncio.gather(*tasks)

    # Split the audio_urls list into a list of lists again, based on the original list
    audio_urls = [
        audio_urls[i : i + len(text_prompts[0])]
        for i in range(0, len(audio_urls), len(text_prompts[0]))
    ]
    return audio_urls


async def generate_audio_urls(audio_prompts):
    audio_url_list = await process_batch(audio_prompts)
    print(audio_url_list)
    return audio_url_list


# # Example usage:
# text_prompts = [
#     "The Estates-General convened in 1789, leading to the formation of the National Assembly, representing the common people's interests.",
#     "The National Constituent Assembly (1789-1791) drafted the Constitution of 1791, establishing a constitutional monarchy.",
#     # Add more text prompts here
# ]

# for i, url in enumerate(audio_urls):
#     if url:
#         print(f"Audio URL for Prompt {i + 1}: {url}")
