from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(tags=["Chat"])

# Configure Google Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

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
"""

@router.post("/chat/message", response_model=ChatResponse)
async def chat_message(request: ChatRequest):
    if not GOOGLE_API_KEY:
        # Fallback for demonstration if no API key is provided
        return ChatResponse(response="Halo! Saya Pera-Bot. (Mode Demo: Mohon maaf, API Key Google Gemini belum dikonfigurasi, sehingga saya hanya bisa menyapa Anda. Silakan hubungi admin untuk aktivasi penuh.)")

    try:
        model = genai.GenerativeModel('gemini-pro')
        
        # Prepare history for Gemini format
        # role: 'user' -> 'user', 'model' -> 'model'
        gemini_history = [
            {"role": "user", "parts": [SYSTEM_INSTRUCTION]},
            {"role": "model", "parts": ["Mengerti. Saya adalah Pera-Bot, asisten AI resmi PERABOX. Saya siap membantu pelanggan dengan informasi layanan kami."]}
        ]
        
        for msg in request.history:
            gemini_history.append({"role": msg.role, "parts": [msg.content]})

        chat = model.start_chat(history=gemini_history)
        response = chat.send_message(request.message)
        
        return ChatResponse(response=response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
