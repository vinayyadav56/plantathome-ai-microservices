from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import (
    ProcessImageRequest, ProcessImageResponse,
    ThumbnailRequest, ThumbnailResponse,
)
from image_processor import process_image, generate_thumbnails
from auth import verify_api_key

app = FastAPI(
    title="PlantAtHome Media Processing Service",
    description="Image optimization, WebP conversion, thumbnail generation, AI background removal, S3 upload",
    version="1.0.0",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "service": "media-service"}


@app.post("/process/image", response_model=ProcessImageResponse)
def process(request: ProcessImageRequest, _: None = Depends(verify_api_key)):
    try:
        return process_image(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/thumbnails", response_model=ThumbnailResponse)
def thumbnails(request: ThumbnailRequest, _: None = Depends(verify_api_key)):
    try:
        return generate_thumbnails(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
