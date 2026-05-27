from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import Plant, SearchRequest, SearchResponse, IndexResponse
from search_service import index_plant, search
from elasticsearch_client import create_plants_index, get_indexed_count
from seed_data import SAMPLE_PLANTS
from auth import verify_api_key
import anthropic


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_plants_index()
    for plant in SAMPLE_PLANTS:
        index_plant(plant)
    yield


app = FastAPI(
    title="PlantAtHome Semantic Search Service",
    description="Natural language plant search — Elasticsearch 8 kNN + Sentence Transformers + Claude reranking",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "semantic-search-service",
        "indexed_plants": get_indexed_count(),
    }


@app.post("/search", response_model=SearchResponse)
def semantic_search(request: SearchRequest, _: None = Depends(verify_api_key)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    try:
        return search(request)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/index", response_model=IndexResponse)
def index_new_plant(plant: Plant, _: None = Depends(verify_api_key)):
    total = index_plant(plant)
    return IndexResponse(
        message=f"Plant '{plant.name}' indexed successfully",
        plant_id=plant.id,
        total_indexed=total,
    )
