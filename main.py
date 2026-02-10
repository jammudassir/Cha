from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import requests
import os


load_dotenv()

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY")
NGROK_PUBLIC_URL = os.getenv("NGROK_PUBLIC_URL", "http://localhost:8000")


DATABASE_URL = "sqlite:///./bonce.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


client = OpenAI(
    base_url="https://ollama.com/v1",
    api_key=OLLAMA_API_KEY,
)


app = FastAPI(title="Bonce AI Backend")

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


class TextRequest(BaseModel):
    prompt: str

class ImageRequest(BaseModel):
    prompt: str



@app.get("/config")
def get_config():
    return {"api_base_url": NGROK_PUBLIC_URL}


@app.post("/generate-text")
def generate_text(request: TextRequest, db: Session = Depends(get_db)):
    response = client.chat.completions.create(
        model="gpt-oss:120b-cloud",
        messages=[
            {"role": "system", "content": VIBE_SYSTEM_PROMPT},
            {"role": "user", "content": request.prompt}
        ],
    )

    ai_text = response.choices[0].message.content


    chat = ChatHistory(
        prompt=request.prompt,
        response=ai_text
    )
    db.add(chat)
    db.commit()

    return {"response": ai_text}


@app.post("/generate-image")
def generate_image(request: ImageRequest):
    try:
        response = requests.post(
            "https://overabusive-cortney-belly.ngrok-free.dev/generate-image",
            json={"prompt": request.prompt}
        )
        return response.json()
    except Exception as e:
        return {"error": str(e)}


@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    chats = db.query(ChatHistory).order_by(ChatHistory.created_at.desc()).all()
    return chats
