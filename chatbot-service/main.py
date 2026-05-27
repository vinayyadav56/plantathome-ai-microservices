from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ChatRequest, ChatResponse, SessionHistoryResponse
from chat_service import chat, get_session_history, clear_session
import anthropic

app = FastAPI(
    title="PlantAtHome AI Chatbot Service",
    description="Memory-based AI plant care assistant powered by Claude",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "chatbot-service"}


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest):
    try:
        return chat(request)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/history/{session_id}", response_model=SessionHistoryResponse)
def get_history(session_id: str):
    return get_session_history(session_id)


@app.delete("/chat/history/{session_id}")
def delete_session(session_id: str):
    clear_session(session_id)
    return {"message": "Session cleared", "session_id": session_id}
