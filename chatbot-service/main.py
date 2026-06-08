from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from models import AskRequest, AskResponse, EndRequest, HealthResponse
from auth import verify_api_key
import ask_service

SWEEP_INTERVAL = int(os.getenv("SWEEP_INTERVAL", "60"))
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]


async def _sweeper():
    """Background flush of abandoned conversations -> one DB row each."""
    while True:
        try:
            await ask_service.sweep_idle()
        except Exception:
            pass
        await asyncio.sleep(SWEEP_INTERVAL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_sweeper())
    yield
    task.cancel()


app = FastAPI(
    title="PlantAtHome Ask-AI Chatbot Service",
    description="Per-plant, topic-scoped AI chat. Async + Redis, built to scale.",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", service="ask-ai-chatbot", redis=await ask_service.redis_ping())


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(request: AskRequest, _=Depends(verify_api_key)):
    try:
        return await ask_service.ask(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/end")
async def end_endpoint(request: EndRequest, _=Depends(verify_api_key)):
    return await ask_service.end(request.conversation_id)
