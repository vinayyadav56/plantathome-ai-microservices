from pydantic import BaseModel
from typing import Optional
from enum import Enum
from datetime import datetime


class EventType(str, Enum):
    search = "search"
    plant_view = "plant_view"
    recommendation_click = "recommendation_click"
    add_to_cart = "add_to_cart"
    purchase = "purchase"
    chatbot_query = "chatbot_query"
    diagnosis_request = "diagnosis_request"


class TrackEventRequest(BaseModel):
    event_type: EventType
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    plant_id: Optional[str] = None
    plant_name: Optional[str] = None
    query: Optional[str] = None
    metadata: dict = {}

    class Config:
        json_schema_extra = {
            "example": {
                "event_type": "search",
                "session_id": "sess_abc123",
                "query": "low maintenance indoor plants",
                "metadata": {"results_count": 5}
            }
        }


class TrendingPlant(BaseModel):
    plant_id: str
    plant_name: str
    view_count: int
    search_appearances: int
    cart_adds: int
    trend_score: float


class SearchBehavior(BaseModel):
    query: str
    count: int
    avg_results: float


class RecommendationPerformance(BaseModel):
    total_recommendations: int
    total_clicks: int
    click_through_rate: float
    top_recommended_plants: list[str]


class AnalyticsSummary(BaseModel):
    period: str
    trending_plants: list[TrendingPlant]
    popular_searches: list[SearchBehavior]
    recommendation_performance: RecommendationPerformance
    total_events: int
