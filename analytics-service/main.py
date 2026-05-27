from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from models import TrackEventRequest, AnalyticsSummary
from analytics_service import create_events_index, track_event, get_summary, get_trending_plants, get_search_behavior
from auth import verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_events_index()
    yield


app = FastAPI(
    title="PlantAtHome Analytics Service",
    description="Event tracking, trending plants, search behavior, recommendation performance",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "analytics-service"}


@app.post("/events")
def track(request: TrackEventRequest, _: None = Depends(verify_api_key)):
    try:
        return track_event(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/summary", response_model=AnalyticsSummary)
def summary(days: int = Query(default=7, ge=1, le=90), _: None = Depends(verify_api_key)):
    try:
        return get_summary(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/trending")
def trending(days: int = Query(default=7, ge=1, le=90), limit: int = Query(default=10, ge=1, le=50), _: None = Depends(verify_api_key)):
    try:
        return get_trending_plants(days, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analytics/searches")
def searches(days: int = Query(default=7, ge=1, le=90), _: None = Depends(verify_api_key)):
    try:
        return get_search_behavior(days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
