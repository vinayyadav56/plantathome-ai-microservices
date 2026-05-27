from pydantic import BaseModel
from typing import Optional
from enum import Enum


class MessageRole(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(BaseModel):
    role: MessageRole
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    language: Optional[str] = "en"

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Why are my leaves turning yellow?",
                "session_id": "user_123_session",
                "language": "en"
            }
        }


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    suggested_products: Optional[list[str]] = None
    follow_up_questions: Optional[list[str]] = None


class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatMessage]
    total_messages: int
