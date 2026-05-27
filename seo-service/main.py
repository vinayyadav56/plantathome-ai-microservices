from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ContentRequest, ContentResponse
from content_service import generate_content
import anthropic

app = FastAPI(
    title="PlantAtHome SEO Content Service",
    description="AI-powered SEO content generation for plant product pages and blogs",
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
    return {"status": "ok", "service": "seo-service"}


@app.post("/generate-content", response_model=ContentResponse)
def create_content(request: ContentRequest):
    try:
        return generate_content(request)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
