from pydantic import BaseModel, Field
from typing import Optional


class PlantContext(BaseModel):
    """Identifies the single plant a conversation is scoped to."""
    id: Optional[int] = None
    name: str
    scientific_name: Optional[str] = None
    # Free-form key facts (care/attributes) the storefront already has, so the
    # model can answer grounded questions without an extra DB hit.
    facts: Optional[str] = None


class AskRequest(BaseModel):
    user_id: int
    plant: PlantContext
    message: str
    conversation_id: Optional[str] = None
    language: Optional[str] = "en"

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 42,
                "plant": {
                    "id": 7,
                    "name": "Monstera Deliciosa",
                    "scientific_name": "Monstera deliciosa",
                    "facts": "Bright indirect light; water when top 2in dry; toxic to pets.",
                },
                "message": "How often should I water it in Mumbai summer?",
                "conversation_id": None,
                "language": "en",
            }
        }


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = "gpt-4o-mini"


class AskResponse(BaseModel):
    reply: str
    conversation_id: str
    prompt_count: int
    limit_reached: bool = False
    usage: TokenUsage = Field(default_factory=TokenUsage)


class EndRequest(BaseModel):
    conversation_id: str


class HealthResponse(BaseModel):
    status: str
    service: str
    redis: str
