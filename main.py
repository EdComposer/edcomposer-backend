import os
import json
import asyncio
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
app = FastAPI()

AUDIO_PROMPT = '''You are tasked with generating nested lists about the given topic. Each nested list will contain details about subtopics in the format [[<detail>,<detail>...],[<detail>,<detail>...]...]. The topic is'''

IMAGE_PROMPT = '''For each input string, determine if the image can easily be found online or if it needs to be generated. Return a dictionary for each string with a 'generate' boolean and a 'prompt' string. The format is [{'generate': <True/False>, 'prompt':<prompt string>}, ...]. The input array is'''

async def async_openai_call(payload):
    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/engines/gpt-4/completions",
                                     headers={"Authorization": f"Bearer {openai_api_key}"},
                                     json=payload)
    return response.json()


@app.get("/video-data")
async def generate_video_data(topic: str):
    audio_response = await async_openai_call({
        "model": "gpt-4",
        "messages": [
            {
                'role': "system",
                "content": AUDIO_PROMPT
            },
            {
                "role": "user",
                "content": topic
            }
        ]
    })

    print(audio_response)
    
    audioGenerationLists = json.loads(audio_response["choices"][0]["message"]["content"])

    image_tasks = [async_openai_call({
        "model": "gpt-4",
        "messages": [
            {
                'role': "system",
                "content": IMAGE_PROMPT
            },
            {
                "role": "user",
                "content": str(audioGenerationList)
            }
        ]
    }) for audioGenerationList in audioGenerationLists]

    image_responses = await asyncio.gather(*image_tasks)
    imageGenerationLists = [json.loads(image_response["choices"][0]["message"]["content"]) for image_response in image_responses]

    videoData = [{"caption": audio, "audio": audio, "image": image} for sublist, img_list in zip(audioGenerationLists, imageGenerationLists) for audio, image in zip(sublist, img_list)]
    
    return {"data": videoData}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
