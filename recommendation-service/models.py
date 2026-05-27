from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class SunlightLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RoomType(str, Enum):
    bedroom = "bedroom"
    living_room = "living_room"
    office = "office"
    balcony = "balcony"
    kitchen = "kitchen"
    bathroom = "bathroom"
    outdoor = "outdoor"


class MaintenanceLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class RecommendationRequest(BaseModel):
    sunlight: SunlightLevel
    room_type: RoomType
    budget: int = Field(..., gt=0, description="Budget in INR")
    pet_friendly: bool = False
    maintenance_level: MaintenanceLevel = MaintenanceLevel.low
    humidity: Optional[str] = None
    aesthetics: Optional[str] = None
    user_experience: Optional[str] = Field(None, description="beginner / intermediate / expert")

    class Config:
        json_schema_extra = {
            "example": {
                "sunlight": "low",
                "room_type": "bedroom",
                "budget": 1000,
                "pet_friendly": True,
                "maintenance_level": "low",
                "user_experience": "beginner"
            }
        }


class PlantRecommendation(BaseModel):
    name: str
    scientific_name: str
    score: float
    price_range: str
    care_difficulty: str
    why_recommended: str
    care_tips: list[str]
    pet_safe: bool


class RecommendationResponse(BaseModel):
    recommendations: list[PlantRecommendation]
    total: int
    query_summary: str
