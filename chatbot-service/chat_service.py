import json
import os
import uuid
import redis
import anthropic
from models import ChatRequest, ChatResponse, ChatMessage, SessionHistoryResponse

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

SESSION_TTL = 3600  # 1 hour

SYSTEM_PROMPT = """You are Planty, PlantAtHome's friendly AI plant care assistant for Indian customers.

Your expertise:
- Plant care advice tailored to Indian climate (monsoon, dry heat, humidity)
- Plant disease diagnosis and solutions
- Fertilizer and watering recommendations
- Answering FAQs about orders and delivery
- Suggesting plants from PlantAtHome's catalog

Guidelines:
- Be warm, friendly, and encouraging
- Give practical advice suited to Indian homes
- Mention Indian seasonal considerations (summer, monsoon, winter)
- If you suggest a product, keep it relevant to plant care
- Keep responses concise and actionable
- Respond in the same language the user writes in (Hindi or English)

When answering, always include 1-2 follow-up questions to continue the conversation."""


def _get_session_key(session_id: str) -> str:
    return f"chat:session:{session_id}"


def _load_history(session_id: str) -> list[dict]:
    key = _get_session_key(session_id)
    raw = redis_client.get(key)
    if raw:
        return json.loads(raw)
    return []


def _save_history(session_id: str, history: list[dict]) -> None:
    key = _get_session_key(session_id)
    redis_client.setex(key, SESSION_TTL, json.dumps(history))


def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid.uuid4())
    history = _load_history(session_id)

    history.append({"role": "user", "content": request.message})

    # Keep last 20 messages to manage context window
    trimmed_history = history[-20:]

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=trimmed_history,
    )

    reply_text = message.content[0].text
    history.append({"role": "assistant", "content": reply_text})
    _save_history(session_id, history)

    # Extract follow-up questions if Claude included them
    follow_ups = _extract_follow_ups(reply_text)

    return ChatResponse(
        reply=reply_text,
        session_id=session_id,
        follow_up_questions=follow_ups,
    )


def get_session_history(session_id: str) -> SessionHistoryResponse:
    history = _load_history(session_id)
    messages = [ChatMessage(role=m["role"], content=m["content"]) for m in history]
    return SessionHistoryResponse(
        session_id=session_id,
        messages=messages,
        total_messages=len(messages),
    )


def clear_session(session_id: str) -> None:
    key = _get_session_key(session_id)
    redis_client.delete(key)


def _extract_follow_ups(text: str) -> list[str]:
    """Best-effort extraction of question lines from the response."""
    lines = text.split("\n")
    questions = [
        line.strip().lstrip("•-* ").strip()
        for line in lines
        if line.strip().endswith("?") and len(line.strip()) > 10
    ]
    return questions[:3] if questions else None
