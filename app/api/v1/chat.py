from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Chat"])

# Configure Google Gemini
from app.core.config import get_settings

settings = get_settings()

# Configure Google Gemini
def configure_genai():
    api_key = os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
    if api_key:
        genai.configure(api_key=api_key)
    return api_key

# Initial config attempt
configure_genai()

class ChatMessage(BaseModel):
    role: str # 'user' or 'model'
    content: str

class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = []

class ChatResponse(BaseModel):
    response: str

# System Prompt for PERABOX
SYSTEM_INSTRUCTION = """
You are "Pera-Bot", the official AI assistant of PERABOX.
PERABOX is a premium homecare service platform in Indonesia.

Our main services are:
1. AC Cleaning (Cuci AC): Starts from Rp 75,000. Comprehensive cleaning of filters, evaporator, and outdoor units.
2. AC Installation (Pasang AC): Starts from Rp 250,000. Professional installation by certified technicians.
3. AC Repair (Perbaikan AC): Price depends on diagnostics. We fix leaks, noise, and AC not cooling.
4. Freon Refill (Isi Freon): Starts from Rp 150,000. Using high-quality refrigerant (R32, R410A).

Brand Voice:
- Professional, helpful, and friendly.
- Language: Primarily Indonesian (Bahasa Indonesia), but can respond in English if asked.
- Call to Action: Encourage users to click "Let's Start" or "Pesan Sekarang" to book a service.

Guidelines:
- If asked about prices not listed above, say that the final price will be determined after technician diagnostics.
- Keep responses concise and easy to read.
- Use emojis occasionally to stay friendly (🏠, ❄️, ✅).
- If the user greeting, reply with a warm welcome and ask how you can help.
"""

@router.get("/chat/models")
async def list_models():
    api_key = configure_genai()
    if not api_key:
        return {"error": "No API key configured"}
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        return {"models": models}
    except Exception as e:
        return {"error": str(e)}

@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    api_key = configure_genai()
    if not api_key:
        return ChatResponse(response="Halo! Saya Pera-Bot. (Mode Debug: GOOGLE_API_KEY tidak ditemukan di environment. Pastikan sudah input di Vercel Settings & Redeploy.)")

    try:
        generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
        
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]

        # Prepare history for Gemini format
        gemini_history = [
            {"role": "user", "parts": [SYSTEM_INSTRUCTION]},
            {"role": "model", "parts": ["Mengerti. Saya adalah Pera-Bot, asisten AI resmi PERABOX. Saya siap membantu pelanggan dengan informasi layanan kami."]}
        ]
        
        for msg in request.history:
            gemini_history.append({"role": msg.role, "parts": [msg.content]})

        # Try to find a working model dynamically
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
            print(f"Available Models: {available_models}")
        except Exception as e:
            print(f"Error listing models: {e}")

        # Priority list
        fav_models = ['models/gemini-1.5-flash', 'models/gemini-1.0-pro', 'models/chat-bison-001']
        model_to_use = None
        
        # 1. Try favorites that are actually in the available list
        for fav in fav_models:
            if fav in available_models:
                model_to_use = fav
                break
        
        # 2. If no favorites found, use any available model
        if not model_to_use and available_models:
            model_to_use = available_models[0]
            
        # 3. Fallback to hardcoded favorite if all else fails
        if not model_to_use:
            model_to_use = 'models/gemini-1.5-flash'

        print(f"Using model: {model_to_use}")
        model = genai.GenerativeModel(
            model_name=model_to_use,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(request.message)
        return ChatResponse(response=response.text)

    except Exception as e:
        error_msg = str(e)
        if "finish_reason" in error_msg and "SAFETY" in error_msg:
             return ChatResponse(response="Maaf, saya tidak dapat menjawab pertanyaan tersebut karena melanggar panduan keamanan kami.")
        
        raise HTTPException(status_code=500, detail=f"AI Error: {str(e)}")
