from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests
import sqlite3


load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_TOKEN = os.getenv("HF_API_TOKEN")
NGROK_PUBLIC_URL = os.getenv("NGROK_PUBLIC_URL", "http://localhost:8000")


DB_FILE = "chat.db"
conn = sqlite3.connect(DB_FILE, check_same_thread=False)
cursor = conn.cursor()


cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender TEXT,
    message TEXT
)
""")


cursor.execute("""
CREATE TABLE IF NOT EXISTS images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    prompt TEXT,
    image_data TEXT
)
""")
conn.commit()


def save_message(sender: str, message: str):
    cursor.execute("INSERT INTO messages (sender, message) VALUES (?, ?)",
        (sender, message)
    )
    conn.commit()


def save_image(prompt: str, image_data: str):
    cursor.execute(
        "INSERT INTO images (prompt, image_data) VALUES (?, ?)",
        (prompt, image_data)
    )
    conn.commit()



client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key=OLLAMA_API_KEY,
)

app = FastAPI()



VIBE_SYSTEM_PROMPT = """
You are an intelligent and proactive AI assistant for 
**Bonce**, an all-in-one digital marketing platform designed to help businesses and creators manage,
automate, and optimize their online presence.
Your role is to support users in planning, executing, tracking,
and analyzing their marketing campaigns across multiple platforms, including social media, content channels,
and advertising networks. You should provide clear, practical,
and actionable guidance that helps users make informed decisions and improve their marketing performance.
Always communicate in a professional, structured, and easy-to-understand manner.
Break down complex concepts when necessary, offer step-by-step recommendations where appropriate,
and prioritize solutions that are efficient, scalable, and aligned with best marketing practices.
"""



class TextRequest(BaseModel):
    prompt: str

class ImageRequest(BaseModel):
    prompt: str

class ToolRequest(BaseModel):
    prompt: str


@app.get("/config")
def get_config():
    return {"api_base_url": NGROK_PUBLIC_URL}


@app.post("/generate-text")
def generate_text(request: TextRequest):

    save_message("user", request.prompt)

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": VIBE_SYSTEM_PROMPT},
            {"role": "user", "content": request.prompt}
        ],
    )

    bot_reply = response.choices[0].message.content


    save_message("bot", bot_reply)

    return {"response": bot_reply}


@app.post("/generate-image")
def generate_image(request: ImageRequest):

    save_message("user", request.prompt)

    try:
        response = requests.post(
            "https://overabusive-cortney-belly.ngrok-free.dev/generate-image",
            json={"prompt": request.prompt}
        )
        res = response.json()


        save_image(request.prompt, str(res))


        save_message("bot", "Image generated and stored in images table")

        return {"image": res}

    except requests.RequestException as e:
        print("Request failed:", e)
        save_message("bot", "Failed to generate image")
        return {"error": "Failed to generate image"}


@app.post("/call-tool")
def call_tool(request: ToolRequest):
    save_message("user", request.prompt)

    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": VIBE_SYSTEM_PROMPT},
            {"role": "user", "content": request.prompt}
        ],
    )

    bot_reply = response.choices[0].message.content
    save_message("bot", bot_reply)

    return {"response": bot_reply}


@app.get("/messages")
def get_messages():
    cursor.execute("SELECT sender, message FROM messages ORDER BY id")
    rows = cursor.fetchall()
    return [{"sender": r[0], "message": r[1]} for r in rows]


@app.get("/images")
def get_images():
    cursor.execute("SELECT id, prompt, image_data FROM images ORDER BY id")
    rows = cursor.fetchall()
    return [
        {"id": r[0], "prompt": r[1], "image_data": r[2]}
        for r in rows
    ]
