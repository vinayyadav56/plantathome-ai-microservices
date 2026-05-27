import os
from datetime import datetime, timezone
from elasticsearch import Elasticsearch
from models import (
    TrackEventRequest, AnalyticsSummary,
    TrendingPlant, SearchBehavior, RecommendationPerformance,
    EventType,
)

EVENTS_INDEX = "plantathome_events"
_client: Elasticsearch | None = None


def get_es() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(os.environ["ELASTICSEARCH_URL"])
    return _client


def create_events_index() -> None:
    es = get_es()
    if es.indices.exists(index=EVENTS_INDEX):
        return
    es.indices.create(
        index=EVENTS_INDEX,
        body={
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
    )


def track_event(request: TrackEventRequest) -> dict:
    es = get_es()
    doc = {
        **request.model_dump(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result = es.index(index=EVENTS_INDEX, document=doc)
    return {"event_id": result["_id"], "status": "tracked"}


def get_trending_plants(days: int = 7, limit: int = 10) -> list[TrendingPlant]:
    es = get_es()
    resp = es.search(
        index=EVENTS_INDEX,
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"terms": {"event_type": ["plant_view", "add_to_cart", "recommendation_click"]}},
                        {"range": {"timestamp": {"gte": f"now-{days}d/d"}}},
                    ]
                }
            },
            "aggs": {
                "by_plant": {
                    "terms": {"field": "plant_id", "size": limit},
                    "aggs": {
                        "plant_name":   {"terms": {"field": "plant_name", "size": 1}},
                        "views":        {"filter": {"term": {"event_type": "plant_view"}}},
                        "cart_adds":    {"filter": {"term": {"event_type": "add_to_cart"}}},
                        "rec_clicks":   {"filter": {"term": {"event_type": "recommendation_click"}}},
                    },
                }
            },
            "size": 0,
        },
    )

    trending = []
    for bucket in resp["aggregations"]["by_plant"]["buckets"]:
        plant_id = bucket["key"]
        name_buckets = bucket["plant_name"]["buckets"]
        plant_name = name_buckets[0]["key"] if name_buckets else plant_id
        views = bucket["views"]["doc_count"]
        cart = bucket["cart_adds"]["doc_count"]
        rec = bucket["rec_clicks"]["doc_count"]
        score = round((views * 1.0 + cart * 3.0 + rec * 2.0) / max(views + cart + rec, 1), 3)

        trending.append(TrendingPlant(
            plant_id=plant_id,
            plant_name=plant_name,
            view_count=views,
            search_appearances=rec,
            cart_adds=cart,
            trend_score=score,
        ))

    return sorted(trending, key=lambda x: x.trend_score, reverse=True)


def get_search_behavior(days: int = 7, limit: int = 20) -> list[SearchBehavior]:
    es = get_es()
    resp = es.search(
        index=EVENTS_INDEX,
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"event_type": "search"}},
                        {"range": {"timestamp": {"gte": f"now-{days}d/d"}}},
                        {"exists": {"field": "query"}},
                    ]
                }
            },
            "aggs": {
                "queries": {
                    "terms": {"field": "query.keyword", "size": limit},
                    "aggs": {
                        "avg_results": {"avg": {"field": "metadata.results_count"}},
                    },
                }
            },
            "size": 0,
        },
    )

    return [
        SearchBehavior(
            query=b["key"],
            count=b["doc_count"],
            avg_results=round(b["avg_results"].get("value") or 0, 1),
        )
        for b in resp["aggregations"]["queries"]["buckets"]
    ]


def get_recommendation_performance(days: int = 7) -> RecommendationPerformance:
    es = get_es()
    resp = es.search(
        index=EVENTS_INDEX,
        body={
            "query": {"range": {"timestamp": {"gte": f"now-{days}d/d"}}},
            "aggs": {
                "total_recommendations": {"filter": {"term": {"event_type": "recommendation_click"}}},
                "top_plants": {
                    "filter": {"term": {"event_type": "recommendation_click"}},
                    "aggs": {"plants": {"terms": {"field": "plant_name", "size": 5}}},
                },
            },
            "size": 0,
        },
    )

    total_rec = resp["aggregations"]["total_recommendations"]["doc_count"]
    top = [b["key"] for b in resp["aggregations"]["top_plants"]["plants"]["buckets"]]

    total_views_resp = es.count(
        index=EVENTS_INDEX,
        body={
            "query": {
                "bool": {
                    "filter": [
                        {"term": {"event_type": "plant_view"}},
                        {"range": {"timestamp": {"gte": f"now-{days}d/d"}}},
                    ]
                }
            }
        },
    )
    total_views = total_views_resp["count"] or 1
    ctr = round(total_rec / total_views, 4)

    return RecommendationPerformance(
        total_recommendations=total_rec,
        total_clicks=total_rec,
        click_through_rate=ctr,
        top_recommended_plants=top,
    )


def get_summary(days: int = 7) -> AnalyticsSummary:
    es = get_es()
    total = es.count(
        index=EVENTS_INDEX,
        body={"query": {"range": {"timestamp": {"gte": f"now-{days}d/d"}}}},
    )["count"]

    return AnalyticsSummary(
        period=f"last_{days}_days",
        trending_plants=get_trending_plants(days),
        popular_searches=get_search_behavior(days),
        recommendation_performance=get_recommendation_performance(days),
        total_events=total,
    )
