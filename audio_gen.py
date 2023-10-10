import os
import boto3
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import aiofiles
import requests
# Load the environment variables
load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")

session = boto3.Session(
    region_name=AWS_DEFAULT_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN
)


polly = session.client("polly", region_name=AWS_DEFAULT_REGION,     aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    aws_session_token=AWS_SESSION_TOKEN)

API_KEY = "12cc955471e5731aadcb000bd6a79ee1"
voice = "en-US-Alex"

async def get_audio(text_prompt):
    # Upload the text to AWS Polly and get the audio file url
    print("Audio currently generating", text_prompt)
    response = requests.post(
    "https://api.elevenlabs.io/tts/synthesize",
    headers={"Authorization": f"Bearer {API_KEY}"},
    json={"text": text_prompt, "voice": voice},
)

    # Generate a unique object key
    object_key = f"{datetime.timestamp(datetime.now())}.mp3"

    try:
        s3 = session.client("s3", region_name=AWS_DEFAULT_REGION)
        BUCKET_NAME = "edcomposer"
        object_key = str(datetime.timestamp(datetime.now())) + ".mp3"

        s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=response.content)
        
        # Generate the download URL for the uploaded file
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_key}"
        
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



# async def try_uploading(byes):
#     s3 = session.client("s3", region_name=AWS_DEFAULT_REGION)
#     BUCKET_NAME = "edcomposer"
#     object_key = str(datetime.timestamp(datetime.now())) + ".mp3"

#     s3.put_object(Bucket=BUCKET_NAME, Key=object_key, Body=byes)
    
#     # Generate the download URL for the uploaded file
#     s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_key}"
    
#     return s3_url




# # try uploading all files in audio folder
# if __name__ == "__main__":
#     for filename in os.listdir("audio"):
#         if filename.endswith(".mp3"):
#             with open("audio/" + filename, "rb") as file:
#                 byes = file.read()
#                 asyncio.run(try_uploading(byes))
#                 continue
#         else:
#             continue