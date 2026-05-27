from pydantic import BaseModel
from typing import Optional
from enum import Enum


class DiagnosisInput(BaseModel):
    image_base64: Optional[str] = None
    image_url: Optional[str] = None
    symptoms: Optional[str] = None
    plant_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "<base64_encoded_image>",
                "symptoms": "Leaves are turning yellow with brown spots",
                "plant_name": "Money Plant"
            }
        }


class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class DiagnosisResult(BaseModel):
    condition: str
    severity: SeverityLevel
    confidence: float
    description: str
    causes: list[str]
    solutions: list[str]
    preventive_measures: list[str]
    products_recommended: Optional[list[str]] = None
    vet_consultation_needed: bool = False


class DiagnosisResponse(BaseModel):
    plant_name: str
    diagnosis: list[DiagnosisResult]
    overall_health_score: float
    immediate_action: str
    long_term_care: str
