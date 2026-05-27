from pydantic import BaseModel
from typing import Optional


class Plant(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    tags: list[str] = []
    sunlight: Optional[str] = None
    maintenance: Optional[str] = None
    pet_friendly: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "plant_001",
                "name": "Snake Plant",
                "description": "Air-purifying indoor plant, great for beginners",
                "category": "indoor",
                "price": 299.0,
                "tags": ["air purifier", "low maintenance", "bedroom"],
                "sunlight": "low",
                "maintenance": "low",
                "pet_friendly": False
            }
        }


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[dict] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "low maintenance plants for bedroom under 500",
                "top_k": 5
            }
        }


class SearchResult(BaseModel):
    plant: Plant
    score: float
    match_reason: str


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
    interpreted_query: str


class IndexResponse(BaseModel):
    message: str
    plant_id: str
    total_indexed: int
