from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import DiagnosisInput, DiagnosisResponse
from diagnosis_service import diagnose
import anthropic

app = FastAPI(
    title="PlantAtHome Plant Doctor Service",
    description="AI-powered plant disease detection and health diagnosis using Claude Vision",
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
    return {"status": "ok", "service": "plant-doctor-service"}


@app.post("/plant-diagnosis", response_model=DiagnosisResponse)
def plant_diagnosis(input_data: DiagnosisInput):
    if not input_data.image_base64 and not input_data.image_url and not input_data.symptoms:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one of: image_base64, image_url, or symptoms"
        )
    try:
        return diagnose(input_data)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
