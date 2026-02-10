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
conn.commit()

def save_message(sender: str, message: str):
    cursor.execute(
        "INSERT INTO messages (sender, message) VALUES (?, ?)",
        (sender, message)
    )
    conn.commit()



client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key=OLLAMA_API_KEY,
)

app = FastAPI()

NGROK_PUBLIC_URL = os.getenv("NGROK_PUBLIC_URL", "http://localhost:8000")



VIBE_SYSTEM_PROMPT = """
You are a smart assistant for Bonce, an all-in-one digital marketing platform. 
Your goal is to help users manage, automate, and analyze their marketing campaigns across multiple social media and content platforms. 
Respond in a professional, helpful, and clear manner. Always prioritize clarity and actionable guidance.
"""

SYSTEM_PROMPT = """
You are a smart assistant specialized in tool-calling. 
"""



class TextRequest(BaseModel):
    prompt: str

class ImageRequest(BaseModel):
    prompt: str

class ToolRequest(BaseModel):
    prompt: str




@app.get("/config")
def get_config():
    return {"api_base_url": NGROK_PUBLIC_URL or "http://127.0.0.1:8000"}

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
    try:
        response = requests.post(
            "https://overabusive-cortney-belly.ngrok-free.dev/generate-image",
            json={"prompt": request.prompt}
        )
        res = response.json()
        return {"image": res}
    except requests.RequestException as e:
        print("Request failed:", e)
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
