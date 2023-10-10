import os
import json
from audio_gen import generate_audio_urls
import picture_gen
import asyncio
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

@app.get("/video-data")
async def generate_video_data(prompt: str):
    audioGenerationLists = json.loads(openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                'role': "system",
                "content": '''
THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
You are an array generator that will return detailed information about a given topic in a nested array format.
You will return NOTHING except a python list with nested lists representing subtopics and containing details about the subtopic.
The details should be strings and each string should be a complete sentence focusing on one idea.
The format to be followed is [[<detail>,<detail>...],[<detail>,<detail>...]...]. The topic is 
'''
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )["choices"][0]["message"]["content"])

    imageGenerationLists = []
    for audioGenerationList in audioGenerationLists:
        imageGenerationList = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    'role': "system",
                    "content": '''
                             THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
                             You are an array generator that will receive an array of strings and generate NOTHING but an array with nested dictionaries (a single dictionary for each string in the input list).
                             Each dictionary should have a boolean field called generate and a string field called prompt.
                             The generate field should be python boolean False if the image can easily be found online OR if it violates policy and python boolean True otherwise.
                             If generate is true then the prompt field should contain a detailed prompt (that follows DALL-E policy) from the input string for image generation, otherwise the prompt field will contain a simplified string for google search.
                             GENERATE THE EXACT SAME AMOUNT OF DICTIONARIES AS THE AMOUNT OF STRINGS IN EACH LIST.
                            The format to be followed is [{'generate': <True/False>, 'prompt':<prompt string>}, {'generate': <True/False>, 'prompt':<prompt string>},...]. The input array is 
                            '''
                },
                {
                    "role": "user",
                    "content": str(audioGenerationList)
                }
            ]
        )["choices"][0]["message"]["content"]

        imageGenerationListParsed = json.loads(imageGenerationList)

        if(len(imageGenerationListParsed)):
            imageGenerationLists.append(imageGenerationListParsed)

    videoData = ""
    for i in range(0, len(audioGenerationLists)):
        audioUrlList = asyncio.run(generate_audio_urls(audioGenerationLists[i]))
        imageUrlList = picture_gen.generatePictures(imageGenerationLists[i])
        currentData = ""

        for j in range(0, len(audioGenerationLists[i])):
            currentData += str({'caption': audioGenerationLists[i][j], 'audio': audioUrlList[j], 'image': imageUrlList[j]})
        
        videoData += "{" + currentData + "},"

    videoData = "{" + videoData + "}"

    print(videoData)
    
    return videoData

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)