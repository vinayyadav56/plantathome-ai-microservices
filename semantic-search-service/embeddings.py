from sentence_transformers import SentenceTransformer

_model: SentenceTransformer | None = None
MODEL_NAME = "all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed(text: str) -> list[float]:
    return get_model().encode(text, normalize_embeddings=True).tolist()


def embed_plant(plant_doc: dict) -> list[float]:
    text = (
        f"{plant_doc['name']}. {plant_doc['description']}. "
        f"Category: {plant_doc['category']}. "
        f"Sunlight: {plant_doc.get('sunlight', 'any')}. "
        f"Maintenance: {plant_doc.get('maintenance', 'any')}. "
        f"Pet friendly: {plant_doc.get('pet_friendly', False)}. "
        f"Tags: {', '.join(plant_doc.get('tags', []))}."
    )
    return embed(text)
