import json
import re
import os
import anthropic
from sentence_transformers import SentenceTransformer
from models import RecommendationRequest, PlantRecommendation, RecommendationResponse
from elasticsearch_client import knn_search_plants

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _build_preference_text(request: RecommendationRequest) -> str:
    return (
        f"plant for {request.room_type} with {request.sunlight} sunlight "
        f"budget {request.budget} rupees "
        f"{'pet friendly ' if request.pet_friendly else ''}"
        f"{request.maintenance_level} maintenance "
        f"{request.user_experience or 'beginner'} gardener "
        f"{request.aesthetics or ''} {request.humidity or ''}"
    )


def _parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON in AI response: {text[:200]}")
    return json.loads(match.group())


SYSTEM_PROMPT = """You are PlantAtHome's expert AI botanist for Indian homes.
You recommend plants available in the Indian market with accurate INR pricing.
Always respond with valid JSON. Prioritize plants that thrive in Indian climate."""


def get_recommendations(request: RecommendationRequest) -> RecommendationResponse:
    # Step 1: embed user preferences and find candidates via Elasticsearch kNN
    pref_text = _build_preference_text(request)
    pref_embedding = _get_model().encode(pref_text, normalize_embeddings=True).tolist()

    es_filters = {
        "pet_friendly": request.pet_friendly if request.pet_friendly else None,
        "sunlight": request.sunlight.value,
        "maintenance": request.maintenance_level.value,
        "max_price": request.budget,
    }
    es_filters = {k: v for k, v in es_filters.items() if v is not None}

    candidates = knn_search_plants(pref_embedding, top_k=10, filters=es_filters)
    candidate_context = ""
    if candidates:
        candidate_context = "\n\nRelevant plants from our catalog (use these as reference):\n"
        candidate_context += "\n".join([
            f"- {c['name']}: {c.get('description', '')} | ₹{c.get('price', 'N/A')}"
            for c in candidates[:5]
        ])

    # Step 2: Claude generates detailed recommendations using candidates as context
    user_prompt = f"""Recommend exactly 5 plants for a customer with these preferences:
- Sunlight: {request.sunlight}
- Room type: {request.room_type}
- Budget: ₹{request.budget}
- Pet friendly required: {request.pet_friendly}
- Maintenance level: {request.maintenance_level}
- Humidity: {request.humidity or 'not specified'}
- Aesthetic preference: {request.aesthetics or 'not specified'}
- Experience level: {request.user_experience or 'beginner'}
{candidate_context}

Return JSON:
{{
  "recommendations": [
    {{
      "name": "Common plant name",
      "scientific_name": "Scientific name",
      "score": 0.95,
      "price_range": "₹200-₹500",
      "care_difficulty": "Easy",
      "why_recommended": "reason",
      "care_tips": ["tip1", "tip2", "tip3"],
      "pet_safe": true
    }}
  ],
  "query_summary": "Brief summary"
}}"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    data = _parse_json(message.content[0].text)
    recommendations = [PlantRecommendation(**r) for r in data["recommendations"]]
    return RecommendationResponse(
        recommendations=recommendations,
        total=len(recommendations),
        query_summary=data["query_summary"],
    )
