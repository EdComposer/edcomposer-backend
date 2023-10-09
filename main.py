import os
import json
from fastapi import FastAPI
from dotenv import load_dotenv
import openai

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

textbookData = '''In 1804, Napoleon Bonaparte crowned himself Emperor of France.
He set out to conquer neighbouring European countries, dispossessing
dynasties and creating kingdoms where he placed members of his family.
Napoleon saw his role as a moderniser of Europe. He introduced many
laws such as the protection of private property and a uniform system of
weights and measures provided by the decimal system. Initially, many
saw Napoleon as a liberator who would bring freedom for the people.
But soon the Napoleonic armies came to be viewed everywhere as an
invading force. He was finally defeated at Waterloo in 1815. Many of his
measures that carried the revolutionary ideas of liberty and modern laws
to other parts of Europe had an impact on people long after Napoleon
had left.
The ideas of liberty and democratic rights were the most important
legacy of the French Revolution. These spread from France to the
rest of Europe during the nineteenth century, where feudal systems were abolished. Colonised peoples reworked the idea of freedom from
bondage into their movements to create a sovereign nation state. Tipu
Sultan and Rammohan Roy are two examples of individuals who
responded to the ideas coming from revolutionary France.'''

app = FastAPI()

@app.get("/generate-mindmap")
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
                "content": textbookData
            }
        ]
    )

    mindMapContent = mindMapOutput["choices"][0]["message"]["content"]
    return json.loads(mindMapContent)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)