import json
import re
import os
import anthropic
from models import Plant, SearchRequest, SearchResponse, SearchResult
from embeddings import embed, embed_plant
from elasticsearch_client import index_plant_document, knn_search, get_indexed_count

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = """You are a plant search AI for PlantAtHome India.
Interpret natural language queries about plants and rerank search results by relevance.
Always respond with valid JSON."""


def index_plant(plant: Plant) -> int:
    doc = plant.model_dump()
    embedding = embed_plant(doc)
    index_plant_document(plant.id, doc, embedding)
    return get_indexed_count()


def _ai_rerank(query: str, candidates: list[dict]) -> dict:
    if not candidates:
        return {"interpreted_query": query, "ranked": []}

    candidate_list = "\n".join([
        f"{i+1}. ID:{c['id']} | {c['name']} | ₹{c['price']} | {c['description'][:80]}"
        for i, c in enumerate(candidates)
    ])

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""User searched: "{query}"

Candidates (already ranked by vector similarity):
{candidate_list}

Rerank by relevance. Return JSON:
{{
  "interpreted_query": "what the user is really looking for",
  "ranked": [
    {{"id": "plant_id", "score": 0.95, "match_reason": "brief explanation"}}
  ]
}}""",
        }],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        # Fallback: return candidates in original order without AI reranking
        return {
            "interpreted_query": query,
            "ranked": [{"id": c["id"], "score": c["score"], "match_reason": "Vector similarity match"} for c in candidates],
        }
    return json.loads(match.group())


def search(request: SearchRequest) -> SearchResponse:
    query_embedding = embed(request.query)
    candidates = knn_search(query_embedding, top_k=10, filters=request.filters)

    if not candidates:
        return SearchResponse(
            query=request.query,
            results=[],
            total=0,
            interpreted_query=request.query,
        )

    ai_result = _ai_rerank(request.query, candidates)

    candidate_map = {c["id"]: c for c in candidates}
    results = []
    for ranked in ai_result.get("ranked", [])[:request.top_k]:
        raw = candidate_map.get(ranked["id"])
        if raw:
            plant = Plant(
                id=raw["id"],
                name=raw["name"],
                description=raw["description"],
                category=raw["category"],
                price=raw["price"],
                tags=raw.get("tags", []),
                sunlight=raw.get("sunlight"),
                maintenance=raw.get("maintenance"),
                pet_friendly=raw.get("pet_friendly"),
            )
            results.append(SearchResult(
                plant=plant,
                score=ranked["score"],
                match_reason=ranked.get("match_reason", ""),
            ))

    return SearchResponse(
        query=request.query,
        results=results,
        total=len(results),
        interpreted_query=ai_result.get("interpreted_query", request.query),
    )
