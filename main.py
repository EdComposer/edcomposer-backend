import os
import json
from audio_gen import generate_audio_urls
import openai
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
import httpx

load_dotenv()

# Set your OpenAI API key from the environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# Define the FastAPI route for generating video data
@app.get("/video-data")
async def generate_video_data(prompt: str):
    print("Received prompt:", prompt)

    # Generate audio information using OpenAI GPT-4
    print("Generating audio...")
    audio_generation_lists = json.loads(openai.ChatCompletion.create(
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

    print("Audio generation completed.")
    print("Received audio_generation_lists:", audio_generation_lists)

    audio_url_list = []

    image_generation_lists = []

    # Process each audio generation list
    for audio_generation_list in audio_generation_lists:
        # Generate image information using OpenAI GPT-4
        print("Generating image for audio generation list...")
        image_generation_list = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    'role': "system",
                    "content": '''THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
                    You are an array generator that will receive an array of strings and generate NOTHING but an array with nested dictionaries (a single dictionary for each string in the input list).
                    Each dictionary should have a boolean field called generate and a string field called prompt.
                    The generate field should be python boolean False if the image can easily be found online OR if it violates policy and python boolean True otherwise.
                    If generate is true then the prompt field should contain a detailed prompt (that follows DALL-E policy) from the input string for image generation, otherwise the prompt field will contain a simplified string for google search.
                    GENERATE THE EXACT SAME AMOUNT OF DICTIONARIES AS THE AMOUNT OF STRINGS IN EACH LIST.
                    The format to be followed is [{"generate": <True/False>, "prompt":<prompt string>}, {"generate": <True/False>, "prompt" :<prompt string>},...]. The input array is '''
                },
                {
                    "role": "user",
                    "content": str(audio_generation_list)
                }
            ]
        )["choices"][0]["message"]["content"]

        print("Image generation completed for audio generation list.")
        print("Generated image_generation_list:", image_generation_list)

        image_generation_list_parsed = json.loads(image_generation_list.replace("True", "true").replace("False", "false"))

        if len(image_generation_list_parsed):
            image_generation_lists.append(image_generation_list_parsed)

    # # Generate audio URLs asynchronously
    # print("Generating audio URLs...")
    # audio_url_list = await generate_audio_urls(audio_generation_lists)
    # print("Audio URLs received:", audio_url_list)

    # Prepare video data
    audioUrlList = await generate_audio_urls(audio_generation_lists)

    imageUrlList = await picGen(image_generation_lists)

    video_data = []

    for audio_urls, image_urls, caption in zip(audioUrlList, imageUrlList, audio_generation_lists):
        current_data = []
        for audio_url,image_url, caption in zip(audio_urls, image_urls, caption):
            current_data.append({
                'caption': caption,
                'audio': audio_url,
                'image': image_url  # Replace with the appropriate image URL
            })

        video_data.append(current_data)

    print("Video data generated.",video_data)

    return video_data


# Additional code for image generation
async def picGen(input: list[list[dict[str, str]]]):
    output = []

    for i in range(0, len(input)):
        currentOutput = []
        for j in range(0, len(input[i])):
            if input[i][j]["generate"]:
                currentOutput.append(await call_dalle_api(input[i][j]["prompt"]))
            else:
                currentOutput.append(await unsplash_it(input[i][j]["prompt"]))
        output.append(currentOutput)

    return output


async def call_dalle_api(prompt):
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {openai.api_key}"},
            json={
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "url",
            },
        )
        print(response)
        print(response.content)
        response = response.json()
        print("DALLE response: " + str(response))
        return response["data"][0]["url"]

async def unsplash_it(query):
    url = f"https://edcomposer.vercel.app/api/getGoogleResult?search={query}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

        return response.json()[0]

# Main function
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=80, reload=True)
