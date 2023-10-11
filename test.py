import httpx


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

    response_json =  response.json()
    print(response_json)
    return response_json[0]
  
import asyncio

async def main():
    print(await unsplash_it("cat"))

asyncio.run(main())



