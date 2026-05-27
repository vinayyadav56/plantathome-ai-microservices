import json
import re
import os
import base64
import httpx
import anthropic
from models import DiagnosisInput, DiagnosisResponse, DiagnosisResult, SeverityLevel

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
PLANT_ID_API_KEY = os.getenv("PLANT_ID_API_KEY", "")
PLANT_ID_URL = "https://api.plant.id/v3/health_assessment"

SYSTEM_PROMPT = """You are Dr. Planty, PlantAtHome's expert AI plant pathologist.
Diagnose plant diseases, nutrient deficiencies, and care issues from images and symptoms.
Deep knowledge of plants in Indian homes and gardens.
Always respond with valid JSON. Recommend solutions available in Indian markets."""

DIAGNOSIS_SCHEMA = """{
  "plant_name": "identified or provided plant name",
  "diagnosis": [
    {
      "condition": "condition name",
      "severity": "low|medium|high|critical",
      "confidence": 0.85,
      "description": "what this condition is",
      "causes": ["cause1", "cause2"],
      "solutions": ["solution1", "solution2"],
      "preventive_measures": ["tip1", "tip2"],
      "products_recommended": ["neem oil", "fungicide"],
      "vet_consultation_needed": false
    }
  ],
  "overall_health_score": 0.65,
  "immediate_action": "what to do right now",
  "long_term_care": "long term recommendation"
}"""


def _fetch_image_bytes(url: str) -> bytes:
    response = httpx.get(url, timeout=10)
    response.raise_for_status()
    return response.content


def _detect_media_type(image_bytes: bytes) -> str:
    if image_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    if image_bytes[:3] == b"GIF":
        return "image/gif"
    return "image/jpeg"


def _media_type_from_base64(b64: str) -> str:
    try:
        return _detect_media_type(base64.b64decode(b64[:20]))
    except Exception:
        return "image/jpeg"


def _call_plant_id(image_base64: str) -> dict | None:
    """Call Plant.id health assessment API for additional disease detection."""
    if not PLANT_ID_API_KEY:
        return None
    try:
        resp = httpx.post(
            PLANT_ID_URL,
            headers={"Api-Key": PLANT_ID_API_KEY, "Content-Type": "application/json"},
            json={"images": [f"data:image/jpeg;base64,{image_base64}"], "similar_images": False},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        return None


def diagnose(input_data: DiagnosisInput) -> DiagnosisResponse:
    messages_content = []
    plant_id_context = ""
    image_base64_str = None

    if input_data.image_base64 or input_data.image_url:
        if input_data.image_base64:
            image_base64_str = input_data.image_base64
            media_type = _media_type_from_base64(image_base64_str)
        else:
            raw_bytes = _fetch_image_bytes(input_data.image_url)
            media_type = _detect_media_type(raw_bytes)
            image_base64_str = base64.b64encode(raw_bytes).decode("utf-8")

        messages_content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_base64_str},
        })

        # Enrich with Plant.id results if API key is available
        plant_id_result = _call_plant_id(image_base64_str)
        if plant_id_result:
            diseases = plant_id_result.get("result", {}).get("disease", {}).get("suggestions", [])
            if diseases:
                plant_id_context = "\n\nPlant.id pre-analysis detected: " + ", ".join(
                    f"{d['name']} (prob: {d.get('probability', 0):.0%})"
                    for d in diseases[:3]
                )

    symptom_text = ""
    if input_data.symptoms:
        symptom_text += f"\nReported symptoms: {input_data.symptoms}"
    if input_data.plant_name:
        symptom_text += f"\nPlant: {input_data.plant_name}"

    messages_content.append({
        "type": "text",
        "text": f"""Diagnose this plant's health issues.{symptom_text}{plant_id_context}

Analyze for: diseases, fungus, overwatering, underwatering, nutrient deficiency, pests, root rot.

Return JSON matching this exact schema:
{DIAGNOSIS_SCHEMA}

Be specific. Recommend solutions available in Indian markets (neem oil, nursery fungicides, etc).""",
    })

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": messages_content}],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in AI response: {text[:200]}")
    data = json.loads(match.group())

    diagnosis_results = [
        DiagnosisResult(
            condition=d["condition"],
            severity=SeverityLevel(d["severity"]),
            confidence=d["confidence"],
            description=d["description"],
            causes=d["causes"],
            solutions=d["solutions"],
            preventive_measures=d["preventive_measures"],
            products_recommended=d.get("products_recommended"),
            vet_consultation_needed=d.get("vet_consultation_needed", False),
        )
        for d in data["diagnosis"]
    ]

    return DiagnosisResponse(
        plant_name=data["plant_name"],
        diagnosis=diagnosis_results,
        overall_health_score=data["overall_health_score"],
        immediate_action=data["immediate_action"],
        long_term_care=data["long_term_care"],
    )
