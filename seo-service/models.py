from pydantic import BaseModel
from typing import Optional
from enum import Enum


class ContentType(str, Enum):
    seo_description = "seo_description"
    blog_post = "blog_post"
    care_instructions = "care_instructions"
    faq = "faq"
    meta_tags = "meta_tags"
    product_title = "product_title"


class ContentRequest(BaseModel):
    plant_name: str
    type: ContentType
    keywords: Optional[list[str]] = None
    tone: Optional[str] = "informative"
    word_count: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "plant_name": "Snake Plant",
                "type": "seo_description",
                "keywords": ["indoor plant", "air purifier", "low maintenance"],
                "tone": "friendly"
            }
        }


class MetaTags(BaseModel):
    title: str
    description: str
    keywords: list[str]
    og_title: str
    og_description: str


class ContentResponse(BaseModel):
    plant_name: str
    content_type: ContentType
    content: str
    meta_tags: Optional[MetaTags] = None
    word_count: int
    seo_score: Optional[float] = None
