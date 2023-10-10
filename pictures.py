import os
from dotenv import load_dotenv
import openai
import requests
import asyncio
import json
import time
import asyncio
import httpx

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


async def picGen(dalle: bool, prompt: str):
    if dalle:
        return await call_dalle_api(prompt)
    else:
        return await unsplash_it(prompt)


async def call_dalle_api(prompt):

    print("running")
    async with httpx.AsyncClient(timeout=90) as client:
        response = await client.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "prompt": prompt,
                "n": 1,
                "size": "1024x1024",
                "response_format": "url",
            },
        )

        response = response.json()

        print("its working x")
        return response["data"][0]["url"]


async def unsplash_it(query):
    url = f"https://edcomposer.vercel.app/api/getGoogleResult?search={query}"
    response = await requests.get(url)
    return response.json()[0]


test_array = [
    "Phases of the Revolution",
    "The Estates-General convened in 1789, leading to the formation of the National Assembly, representing the common people's interests.",
    "The National Constituent Assembly (1789-1791) drafted the Constitution of 1791, establishing a constitutional monarchy.",
    "The Radical Phase (1792-1794) witnessed events like the Reign of Terror, mass executions, and the fall of the monarchy.",
    "The Directory (1795-1799) faced political turbulence, setting the stage for Napoleon Bonaparte's rise.",
    "Napoleon's ascent in 1799 marked the Revolution's culmination and the establishment of the Consulate.",
    "Key Figures",
    "Maximilien Robespierre, a leader of the radical Jacobins, advocated revolutionary justice during the Reign of Terror.",
    "The execution of King Louis XVI by guillotine in 1793 symbolized a critical moment in the Revolution.",
    "Napoleon Bonaparte, a skilled military general, rose to power and declared himself Emperor, introducing the Napoleonic Code.",
]

return_array = []


async def process_data(inp_array):
    start = time.time()
    
    tasks = [call_dalle_api(prompt) for prompt in inp_array]
    return_array = await asyncio.gather(*tasks)
    end = time.time()
    print(end - start)
    return return_array


loop = asyncio.get_event_loop()
return_array = loop.run_until_complete(process_data(test_array))

print(return_array)