import os
import requests
from dotenv import load_dotenv
import boto3
from datetime import datetime

#load the environment variables
load_dotenv()

AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION")
REMOTION_AWS_ACCESS_KEY_ID = os.getenv("REMOTION_AWS_ACCESS_KEY_ID")
REMOTION_AWS_SECRET_ACCESS_KEY = os.getenv("REMOTION_AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")


session = boto3.Session(profile_name="dhanush")
polly = session.client("polly", region_name=AWS_DEFAULT_REGION)
s3 = boto3.client("s3", region_name=AWS_DEFAULT_REGION,
                      aws_access_key_id=REMOTION_AWS_ACCESS_KEY_ID,
                      aws_secret_access_key=REMOTION_AWS_SECRET_ACCESS_KEY,
                      aws_session_token=AWS_SESSION_TOKEN)
def getAudio(textPrompt):
    #upload the text to aws polly and get the audio file url
    polly = boto3.client("polly", region_name=AWS_DEFAULT_REGION, aws_access_key_id=REMOTION_AWS_ACCESS_KEY_ID, aws_secret_access_key=REMOTION_AWS_SECRET_ACCESS_KEY, aws_session_token=AWS_SESSION_TOKEN)
    response = polly.synthesize_speech(VoiceId='Joanna', OutputFormat='mp3', Text = textPrompt)
    file_path = "response.mp3"
    file = open(file_path, 'wb')
    file.write(response['AudioStream'].read())
    file.close()
    audio_url = uploadFileToS3(file_path)
    return audio_url

def uploadFileToS3(file_path):
    
    bucket_name = "edcomposer"
    object_key = str(datetime.timestamp(datetime.now())) + ".mp3"

    try:
        s3.upload_file(file_path, bucket_name, object_key)
        
        # Generate the download URL for the uploaded file
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{object_key}"

        # Delete the file from the local directory
        os.remove(file_path)
        
        return s3_url

    except Exception as e:
        print(f"Error uploading to S3: {e}")
        return None

 
audio_url = getAudio("The Estates-General convened in 1789, leading to the formation of the National Assembly, representing the common people's interests.")
if audio_url:
    print(f"Audio URL: {audio_url}")
