"""
Run once to initialise all Elasticsearch indices.
Called automatically at startup by semantic-search-service and analytics-service.
Can also be run manually: python init_indices.py
"""
import os
import sys
from elasticsearch import Elasticsearch

ES_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
EMBEDDING_DIM = 384

INDICES = {
    "plantathome_plants": {
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
    "plantathome_events": {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "event_type":  {"type": "keyword"},
                "user_id":     {"type": "keyword"},
                "session_id":  {"type": "keyword"},
                "plant_id":    {"type": "keyword"},
                "plant_name":  {"type": "keyword"},
                "query":       {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
                "timestamp":   {"type": "date"},
                "metadata":    {"type": "object", "dynamic": True},
            }
        },
    },
}


def init(es_url: str = ES_URL) -> None:
    es = Elasticsearch(es_url)
    for name, body in INDICES.items():
        if es.indices.exists(index=name):
            print(f"  [skip] index '{name}' already exists")
        else:
            es.indices.create(index=name, body=body)
            print(f"  [ok]   index '{name}' created")


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else ES_URL
    print(f"Initialising Elasticsearch indices at {url}...")
    init(url)
    print("Done.")
