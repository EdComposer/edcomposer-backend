import os
import json

import requests
from audio_gen import generate_audio_urls
import openai
import asyncio
from fastapi import FastAPI
from dotenv import load_dotenv
import httpx

from d import generate_metadata

load_dotenv()

# Set your OpenAI API key from the environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()


# Define the FastAPI route for generating video data
@app.get("/video-data")
@app.get("/video-data")
async def generate_video_data(prompt: str):
    print("Received prompt:", prompt)

    # Generate audio information using OpenAI GPT-4
    print("Generating audio...")
    audio_generation_lists = json.loads(
        openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": """
THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
                You are an array generator that will return detailed information about a given topic in a nested array format.
                You will return NOTHING except a python list with nested lists representing subtopics and containing details about the subtopic.
                The details should be strings and each string should be a complete sentence focusing on one idea.
                The format to be followed is [[<detail>,<detail>...],[<detail>,<detail>...]...]. The topic is 
                """,
                },
                {"role": "user", "content": prompt},
            ],
        )["choices"][0]["message"]["content"]
    )

    print("Audio generation completed.")
    print("Received audio_generation_lists:", audio_generation_lists)

    image_generation_lists = []

    # for every element in the audio_generation_lists, ask openai to generate a dictoinary with a boolean field called generate and a string field called prompt
    for audio_generation_list in audio_generation_lists:
        image_generation_list = []
        print(audio_generation_list)
        for audio_generation in audio_generation_list:
            image_dict = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """THE MOST IMPORTANT THING IS TO RETURN ONLY TEXT THAT CAN BE PARSED AS JSON, IT NEEDS TO BE A VALID JSON STRING SO DO NOT INCLUDE ANY OTHER EXTRA INFORMATION AT ALL.
                        You are a dictionary generator that has to output if the image can be found online or not and a prompt for the image generation.
                    Each dictionary should have a boolean field called generate and a string field called prompt.
                    The generate field should be python boolean False if the image can easily be found online OR if it violates policy and python boolean True otherwise.
                    If generate is true then the prompt field should contain a detailed prompt (that follows DALL-E policy) from the input string for image generation, otherwise the prompt field will contain a simplified string for google search.
                    GENERATE THE EXACT SAME AMOUNT OF DICTIONARIES AS THE AMOUNT OF STRINGS IN the LIST.
                    The format to be followed is {"generate": <true/false>, "prompt":<prompt string>} """,
                    },
                    {"role": "user", "content": audio_generation},
                ],
            )["choices"][0]["message"]["content"]
            print(image_dict)
            image_dict = json.loads(
                image_dict.replace("True", "true").replace("False", "false")
            )
            print(image_dict)

            image_generation_list.append(image_dict)
        image_generation_lists.append(image_generation_list)
        print("Image dict:", image_generation_list)

    # # Generate audio URLs asynchronously
    # print("Generating audio URLs...")
    # audio_url_list = await generate_audio_urls(audio_generation_lists)

    # Prepare video data
    audioUrlList = await generate_audio_urls(audio_generation_lists)
    print("This is audioUrlList", audioUrlList)

    print("This is subtitle list", audio_generation_lists)

    imageUrlList = await picGen(image_generation_lists)
    print("This is imageUrlList", imageUrlList)
    formatted_data = {"sequences": []}
    # create a list of dictionaries for each item in the audio_generation_lists that contains the audio url, image url, and caption
    for audio_urls, audio_texts, image_data in zip(audioUrlList, audio_generation_lists, imageUrlList):
        sequence = []

        for audio_url, audio_text, image_info in zip(audio_urls, audio_texts, image_data):
            sequence.append({
                "caption": audio_text,
                "audio": audio_url,
                "image": extractImage(image_info)[0]
            })

        formatted_data["sequences"].append(sequence)
   

    # for audio_urls, image_urls, caption in zip(audioUrlList, imageUrlList, audio_generation_lists):
    #     current_data = []
    #     for i in range(len(caption)):
    #         current_data.append(
    #             {
    #                 "audio_url": audio_urls[i],
    #                 "image_url": image_urls[i],
    #                 "caption": caption[i],
    #             }
    #         )
    #     video_data.append(current_data)

    formatted_data["metadata"] =   await generate_metadata(prompt)

    print("Video data generated.", formatted_data)
    return formatted_data


#I want to traverse to image_generation_lists and then for each element in the list, i want to call the picGen function. I want to do this for each element in the list when i dont know the dimension of the list 

async def picGen(input_list):
    finalList = []

    for i in input_list:
        if isinstance(i, dict):
            l = []
            if i["generate"]:
                image_url = await call_dalle_api(i["prompt"])
                l.append({"image_url": image_url})
            else:
                image_url = await unsplash_it(i["prompt"])
                l.append({"image_url": image_url})
            finalList.append(l)
        elif isinstance(i, list):
            # Recursively call picGen on sublists
            sublist_result = await picGen(i)
            finalList.append(sublist_result)

    return finalList

def extractImage(input_list):
     finalList = []

     for i in input_list:
         if isinstance(i, dict):
             l = []
              
             finalList.append(i["image_url"])
         elif isinstance(i, list):
              # Recursively call picGen on sublists
             finalList.append(i)

     return finalList

      
    
      



# async def picGen(input_json, finalURLList: list):
#   """Recursively generates image URLs for the given input JSON.

#   Args:
#     input_json: A list of dictionaries, where each dictionary contains a "generate"
#       boolean field and a "prompt" string field.
#     finalURLList: A list of lists of image URLs.

#   Returns:
#     None.
#   """

#   for dictionary in input_json:
#     if isinstance(dictionary, dict):
#       if dictionary["generate"]:
#         image_url = await call_dalle_api(dictionary["prompt"])
#         finalURLList.append([image_url])
#       else:
#         image_url = await unsplash_it(dictionary["prompt"])
#         finalURLList.append([image_url])
#     else:
#       await picGen(dictionary, finalURLList)


async def call_dalle_api(prompt):
  """Generates an image URL using the DALL-E API.

  Args:
    prompt: A string containing the prompt for the image.

  Returns:
    A string containing the image URL, or None if the API fails.
  """

  async with httpx.AsyncClient(timeout=120) as client:
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

    if response.status_code != 200:
      return None

    response_json = response.json()
    return response_json["data"][0]["url"]


async def unsplash_it(query):
  """Generates an image URL using the Unsplash API.

  Args:
    query: A string containing the query for the image.

  Returns:
    A string containing the image URL, or None if the API fails.
  """

  async with httpx.AsyncClient() as client:
    response = await client.get(f"https://edcomposer.vercel.app/api/getGoogleResult?search={query}")

    if response.status_code != 200:
      return None

    # Get parsable JSON from the response
    response_json = response.json()

    return response_json[0]


# Main function
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", reload=True)
