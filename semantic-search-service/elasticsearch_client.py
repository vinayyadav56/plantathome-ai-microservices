import os
from elasticsearch import Elasticsearch

PLANTS_INDEX = "plantathome_plants"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension

_client: Elasticsearch | None = None


def get_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(os.environ["ELASTICSEARCH_URL"])
    return _client


def create_plants_index() -> None:
    es = get_client()
    if es.indices.exists(index=PLANTS_INDEX):
        return

    es.indices.create(
        index=PLANTS_INDEX,
        body={
            "settings": {"number_of_shards": 1, "number_of_replicas": 0},
            "mappings": {
                "properties": {
                    "id":           {"type": "keyword"},
                    "name":         {"type": "text", "analyzer": "standard"},
                    "description":  {"type": "text", "analyzer": "standard"},
                    "category":     {"type": "keyword"},
                    "price":        {"type": "float"},
                    "tags":         {"type": "keyword"},
                    "sunlight":     {"type": "keyword"},
                    "maintenance":  {"type": "keyword"},
                    "pet_friendly": {"type": "boolean"},
                    "embedding": {
                        "type": "dense_vector",
                        "dims": EMBEDDING_DIM,
                        "index": True,
                        "similarity": "cosine",
                    },
                }
            },
        },
    )


def index_plant_document(plant_id: str, doc: dict, embedding: list[float]) -> None:
    es = get_client()
    es.index(index=PLANTS_INDEX, id=plant_id, document={**doc, "embedding": embedding})


def knn_search(
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
        if "max_price" in filters:
            filter_clauses.append({"range": {"price": {"lte": filters["max_price"]}}})
        if "pet_friendly" in filters:
            filter_clauses.append({"term": {"pet_friendly": filters["pet_friendly"]}})
        if "category" in filters:
            filter_clauses.append({"term": {"category": filters["category"]}})
        if "sunlight" in filters:
            filter_clauses.append({"term": {"sunlight": filters["sunlight"]}})
        if "maintenance" in filters:
            filter_clauses.append({"term": {"maintenance": filters["maintenance"]}})

    if filter_clauses:
        knn_query["filter"] = {"bool": {"must": filter_clauses}}

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


def get_indexed_count() -> int:
    es = get_client()
    try:
        result = es.count(index=PLANTS_INDEX)
        return result["count"]
    except Exception:
        return 0
