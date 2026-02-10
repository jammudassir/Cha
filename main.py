from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from openai import OpenAI
from ollama import chat 
import json
import requests
  
load_dotenv()



OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
HF_TOKEN = os.getenv("HF_API_TOKEN")  

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

Responsibilities:
- Help users connect social media and content accounts (Facebook, Instagram, LinkedIn, Reddit, TikTok, Twitter (X), YouTube, WordPress, Notion, and more).
- Troubleshoot connection or authentication issues.
- Assist users in creating, scheduling, editing, and tracking posts and campaigns.
- Suggest optimal posting times, formats, and engagement tips.
- Guide users to write, edit, and organize blog posts, emails, and social media content.
- Generate content ideas for campaigns, posts, and blogs.
- Recommend hashtags, keywords, or strategies for higher engagement.
- Explain analytics, metrics, and campaign performance insights.
- Assist in managing user accounts, roles, and permissions.
- Guide admins on subscription plans, billing, and usage limits.
- Help with email campaigns and chatbot creation.
- Explain dashboard UI, tables, cards, and interactive components.
- Always give clear step-by-step instructions and actionable guidance.
- Ask clarifying questions if information is missing.
- Keep responses professional, concise, and encouraging.

Example queries you may respond to:
- "How do I schedule a post on TikTok and Instagram at the same time?"
- "Can you suggest a content idea for my email campaign about product launches?"
- "I want to add a new team member and give them limited permissions."
- "Show me my last week"s campaign performance."

Behavior:
- Be proactive in suggesting best practices and improvements.
- Provide AI-generated content or strategies when asked.
- Always keep responses actionable and easy to follow.

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
        response = client.chat.completions.create(
            model="gpt-oss:120b-cloud",
            messages=[
                {"role": "system", "content": VIBE_SYSTEM_PROMPT},
                {"role": "user", "content": request.prompt}
            ],
        )
        return {"response": response.choices[0].message.content}


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
        resposne = client.chat.completions.create(
            model="gpt-oss:120b-cloud",
            messages=[
                {"role": "system", "content": VIBE_SYSTEM_PROMPT},
                {"role":"user","content": request.prompt}
            ],
        )
        return {"response": resposne.choices[0].message.content}




