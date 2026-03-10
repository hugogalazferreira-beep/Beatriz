import os
import base64
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from google import genai
from google.genai import types
from dotenv import load_dotenv
import requests

load_dotenv()

app = FastAPI(title="Beatriz AI Assistant API")

# Configure CORS
origins = [
    "https://hugogalaz.lovable.app",
    "http://localhost:8000",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
client = None
if api_key:
    client = genai.Client(api_key=api_key)
else:
    print("Warning: GEMINI_API_KEY not found in environment variables.")

# ElevenLabs Config
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Default Rachel or PT voice

SYSTEM_PROMPT = (
    "You are Beatriz, the AI sales and qualification assistant for Hugo Galaz (Consultant in IT, Cybersecurity, and AI with over 25 years of experience).\n"
    "Your language is strictly European Portuguese (PT-PT).\n"
    "Your tone is professional, helpful, and concise (never write more than 2 short paragraphs per response).\n\n"
    "Your Main Goal: Qualify website visitors and schedule qualified meetings via Calendly.\n\n"
    "Hugo's Core Offers:\n"
    "1. Fast Cashflow Offer: Professional websites delivered in 24 hours starting at 475€.\n"
    "2. Retainer Offer: Strategic IT & AI Consulting (Fractional CTO, cybersecurity, AI automation) via 'Bancos de Horas' (10h, 20h, or 40h/month).\n\n"
    "Conversation Rules:\n"
    "- Greeting: Start by warmly welcoming the user and immediately asking: 'Olá! Sou a Beatriz, assistente virtual do Hugo Galaz. Para o encaminhar da melhor forma, diga-me: qual é o principal bloqueio tecnológico ou operacional que a sua empresa enfrenta hoje?'\n"
    "- Handling Website Requests: If the user mentions needing a website, digital presence, or a landing page, present the 'Sites profissionais em 24h a partir de 475€' and ask if they want to schedule a quick call to define the project.\n"
    "- Handling IT/AI/Security Requests: If they mention disorganization, need for automation, AI, or cybersecurity, validate their pain point. Mention Hugo's 25 years of experience and offer a 'Sessão de Diagnóstico Gratuita de 15 minutos' to see how Hugo's Consulting and 'Bancos de Horas' can solve it.\n"
    "- Booking the Meeting: The moment the user agrees to a meeting or wants to speak with Hugo, provide this link: https://app.clickup.com/90152413362/calendar\n"
    "- Guardrails: Do not invent prices or services. If asked something complex, say you will schedule a meeting with Hugo so he can provide a technical answer."
)

class Message(BaseModel):
    role: str
    parts: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Message]] = []

def text_to_speech_base64(text: str) -> Optional[str]:
    if not ELEVENLABS_API_KEY:
        return None

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }

    try:
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode('utf-8')
        else:
            print(f"ElevenLabs Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"ElevenLabs Exception: {e}")
        return None

@app.get("/")
async def root():
    return {"message": "Beatriz AI Assistant API is running"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Gemini API key not configured")

    try:
        chat_history = []
        for msg in request.history:
            chat_history.append(types.Content(
                role=msg.role,
                parts=[types.Part(text=msg.parts)]
            ))

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=chat_history + [types.Content(role="user", parts=[types.Part(text=request.message)])],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT
            )
        )

        text_response = response.text
        audio_base64 = text_to_speech_base64(text_response)

        return {
            "response": text_response,
            "audio_base64": audio_base64,
            "history": request.history + [
                Message(role="user", parts=request.message),
                Message(role="model", parts=text_response)
            ]
        }
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
