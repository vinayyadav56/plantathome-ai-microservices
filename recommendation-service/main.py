from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import RecommendationRequest, RecommendationResponse
from ai_service import get_recommendations
from auth import verify_api_key
import anthropic

app = FastAPI(
    title="PlantAtHome Recommendation Service",
    description="AI plant recommendations — Elasticsearch kNN + Sentence Transformers + Claude",
    version="2.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "recommendation-service"}


@app.post("/recommendations", response_model=RecommendationResponse)
def recommend_plants(request: RecommendationRequest, _: None = Depends(verify_api_key)):
    try:
        return get_recommendations(request)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
