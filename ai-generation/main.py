import os
import json
from fastapi import FastAPI
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

inputData = "French Revolution"

app = FastAPI()

@app.get("/frame-json")
async def generate_mindmap():
    mindMapOutput = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                'role': "system",
                "content": '''You are a mind map generator. Your role is to output a mind map of the given data in JSON format. The format should be like {"node":[{"title": <title>, "info": [<info-point>, <info-point>], "node": [...]}, {"title": <title>, "info": [<info-point>,<info-point>]}]...}. Nest the JSON whenever necessary (for example, when there are subtopics under a topic). Be detail-oriented, standardized but crisp. The given data is'''
            },
            {
                "role": "user",
                "content": inputData
            }
        ]
    )

    mindMapContent = mindMapOutput["choices"][0]["message"]["content"]
    return json.loads(mindMapContent)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)