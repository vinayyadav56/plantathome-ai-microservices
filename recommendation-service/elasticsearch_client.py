import os
from elasticsearch import Elasticsearch

PLANTS_INDEX = "plantathome_plants"
EMBEDDING_DIM = 384


def get_client() -> Elasticsearch:
    return Elasticsearch(os.environ["ELASTICSEARCH_URL"])


def knn_search_plants(
    query_embedding: list[float],
    top_k: int = 10,
    filters: dict | None = None,
) -> list[dict]:
    es = get_client()

    knn_query = {
        "field": "embedding",
        "query_vector": query_embedding,
        "k": top_k,
        "num_candidates": top_k * 5,
    }

    filter_clauses = []
    if filters:
        if filters.get("pet_friendly"):
            filter_clauses.append({"term": {"pet_friendly": True}})
        if filters.get("sunlight"):
            filter_clauses.append({"term": {"sunlight": filters["sunlight"]}})
        if filters.get("maintenance"):
            filter_clauses.append({"term": {"maintenance": filters["maintenance"]}})
        if filters.get("max_price"):
            filter_clauses.append({"range": {"price": {"lte": filters["max_price"]}}})

    if filter_clauses:
        knn_query["filter"] = {"bool": {"must": filter_clauses}}

    try:
        response = es.search(
            index=PLANTS_INDEX,
            knn=knn_query,
            size=top_k,
            source_excludes=["embedding"],
        )
        return [
            {"id": hit["_id"], "score": hit["_score"], **hit["_source"]}
            for hit in response["hits"]["hits"]
        ]
    except Exception:
        return []
