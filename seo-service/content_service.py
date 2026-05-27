import json
import re
import os
import hashlib
import redis
import anthropic
from models import ContentRequest, ContentResponse, ContentType, MetaTags

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

CACHE_TTL = 86400  # 24 hours

SYSTEM_PROMPT = """You are PlantAtHome's expert SEO content writer for the Indian plant e-commerce market.
You create compelling, SEO-optimized content that ranks on Google India.
Use Indian English, mention Indian climate/seasons where relevant.
Always respond with valid JSON matching the schema provided."""

CONTENT_PROMPTS = {
    ContentType.seo_description: """Write an SEO-optimized product description for {plant_name}.
Keywords to include naturally: {keywords}
Tone: {tone}
Target word count: {word_count}

Return JSON:
{{
  "content": "The full product description here",
  "meta_tags": {{
    "title": "SEO title (60 chars max)",
    "description": "Meta description (160 chars max)",
    "keywords": ["kw1", "kw2", "kw3"],
    "og_title": "Social share title",
    "og_description": "Social share description"
  }},
  "seo_score": 0.85
}}""",

    ContentType.blog_post: """Write a helpful blog post about {plant_name} for Indian plant enthusiasts.
Keywords: {keywords}
Tone: {tone}
Target word count: {word_count}

Include: introduction, care tips, common problems, why to buy from PlantAtHome.
Return JSON:
{{
  "content": "Full blog post in markdown",
  "meta_tags": {{
    "title": "Blog title",
    "description": "Meta description",
    "keywords": ["kw1", "kw2"],
    "og_title": "Social title",
    "og_description": "Social description"
  }},
  "seo_score": 0.80
}}""",

    ContentType.care_instructions: """Write detailed care instructions for {plant_name} suitable for Indian homes.
Return JSON:
{{
  "content": "Detailed care guide in markdown",
  "seo_score": 0.75
}}""",

    ContentType.faq: """Generate 8 frequently asked questions and answers about {plant_name} for Indian customers.
Return JSON:
{{
  "content": "FAQ in markdown Q&A format",
  "seo_score": 0.70
}}""",

    ContentType.meta_tags: """Generate complete SEO meta tags for {plant_name} product page.
Keywords: {keywords}
Return JSON:
{{
  "content": "",
  "meta_tags": {{
    "title": "Title (60 chars max)",
    "description": "Description (160 chars max)",
    "keywords": ["kw1", "kw2", "kw3", "kw4", "kw5"],
    "og_title": "OG title",
    "og_description": "OG description"
  }},
  "seo_score": 0.90
}}""",

    ContentType.product_title: """Generate 5 SEO-optimized product title variations for {plant_name}.
Return JSON:
{{
  "content": "Primary title\\n---\\nAlternative 1\\nAlternative 2\\nAlternative 3\\nAlternative 4",
  "seo_score": 0.85
}}""",
}


def _cache_key(request: ContentRequest) -> str:
    raw = f"{request.plant_name}:{request.type}:{request.keywords}:{request.tone}:{request.word_count}"
    return f"seo:content:{hashlib.md5(raw.encode()).hexdigest()}"


def generate_content(request: ContentRequest) -> ContentResponse:
    cache_key = _cache_key(request)
    cached = redis_client.get(cache_key)
    if cached:
        data = json.loads(cached)
        return ContentResponse(**data)

    word_count = request.word_count or 300
    keywords_str = ", ".join(request.keywords) if request.keywords else "indoor plants India"

    prompt_template = CONTENT_PROMPTS.get(request.type, CONTENT_PROMPTS[ContentType.seo_description])
    prompt = prompt_template.format(
        plant_name=request.plant_name,
        keywords=keywords_str,
        tone=request.tone or "informative",
        word_count=word_count,
    )

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",  # Use cheaper model for SEO content
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in AI response: {text[:200]}")
    data = json.loads(match.group())

    meta = None
    if "meta_tags" in data and data["meta_tags"]:
        meta = MetaTags(**data["meta_tags"])

    content = data.get("content", "")
    response = ContentResponse(
        plant_name=request.plant_name,
        content_type=request.type,
        content=content,
        meta_tags=meta,
        word_count=len(content.split()),
        seo_score=data.get("seo_score"),
    )

    redis_client.setex(cache_key, CACHE_TTL, response.model_dump_json())
    return response
