# PlantAtHome AI Microservices — API Documentation

**Version:** 2.0.0  
**Base URL (via nginx gateway):** `http://your-domain.com`  
**Direct service ports:** see individual service sections  

---

## Table of Contents

1. [Authentication](#1-authentication)
2. [Global Error Codes](#2-global-error-codes)
3. [Recommendation Service](#3-recommendation-service)
4. [AI Chatbot Service](#4-ai-chatbot-service)
5. [Plant Doctor Service](#5-plant-doctor-service)
6. [SEO Content Service](#6-seo-content-service)
7. [Semantic Search Service](#7-semantic-search-service)
8. [Notification Service](#8-notification-service)
9. [Media Processing Service](#9-media-processing-service)
10. [Analytics Service](#10-analytics-service)
11. [Laravel Integration Reference](#11-laravel-integration-reference)
12. [RabbitMQ Queue Schema](#12-rabbitmq-queue-schema)

---

## 1. Authentication

All endpoints (except `/health`) require the `X-Api-Key` header.

```http
X-Api-Key: your_service_api_key_here
Content-Type: application/json
```

| Header | Required | Description |
|--------|----------|-------------|
| `X-Api-Key` | Yes | Service API key set in `.env` as `SERVICE_API_KEY` |
| `Content-Type` | Yes | Must be `application/json` |

**Unauthorized response (401):**
```json
{
  "detail": "Invalid or missing X-Api-Key header"
}
```

---

## 2. Global Error Codes

| HTTP Code | Meaning |
|-----------|---------|
| `200` | Success |
| `400` | Bad request — validation error or missing required field |
| `401` | Unauthorized — invalid or missing API key |
| `422` | Unprocessable entity — request body schema mismatch |
| `500` | Internal server error |
| `502` | AI service (Claude/Plant.id) returned an error |

---

## 3. Recommendation Service

**Direct port:** `8001`  
**Gateway path:** `/api/recommendations`

AI-powered plant recommendations using Elasticsearch kNN vector search + Claude reasoning, tailored for Indian homes.

---

### `GET /health`

Check service health.

**Response:**
```json
{
  "status": "ok",
  "service": "recommendation-service"
}
```

---

### `POST /recommendations`

Get personalized plant recommendations based on user preferences.

**Request Body:**

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `sunlight` | string | ✅ | `low` \| `medium` \| `high` |
| `room_type` | string | ✅ | `bedroom` \| `living_room` \| `office` \| `balcony` \| `kitchen` \| `bathroom` \| `outdoor` |
| `budget` | integer | ✅ | Amount in INR (e.g. `1000`) |
| `pet_friendly` | boolean | ❌ | Default: `false` |
| `maintenance_level` | string | ❌ | `low` \| `medium` \| `high` — Default: `low` |
| `humidity` | string | ❌ | Free text (e.g. `"dry"`, `"humid"`) |
| `aesthetics` | string | ❌ | Free text (e.g. `"modern"`, `"tropical"`) |
| `user_experience` | string | ❌ | `beginner` \| `intermediate` \| `expert` |

**Example Request:**
```bash
curl -X POST http://localhost:8001/recommendations \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "sunlight": "low",
    "room_type": "bedroom",
    "budget": 1000,
    "pet_friendly": true,
    "maintenance_level": "low",
    "user_experience": "beginner"
  }'
```

**Response:**
```json
{
  "recommendations": [
    {
      "name": "Spider Plant",
      "scientific_name": "Chlorophytum comosum",
      "score": 0.96,
      "price_range": "₹200-₹400",
      "care_difficulty": "Easy",
      "why_recommended": "Thrives in low light, completely pet-safe, and requires watering only once a week.",
      "care_tips": [
        "Water once a week, let soil dry between waterings",
        "Avoid direct sunlight — indirect light is ideal",
        "Mist leaves during dry Indian summers"
      ],
      "pet_safe": true
    }
  ],
  "total": 5,
  "query_summary": "Low-light, pet-safe bedroom plant under ₹1000 for a beginner"
}
```

---

## 4. AI Chatbot Service

**Direct port:** `8002`  
**Gateway path:** `/api/chat`

Memory-based plant care assistant "Planty" — supports Hindi and English, retains conversation history per session using Redis.

---

### `GET /health`

```json
{ "status": "ok", "service": "chatbot-service" }
```

---

### `POST /chat`

Send a message to the plant care AI assistant.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `message` | string | ✅ | User's question or message |
| `session_id` | string | ❌ | Reuse to continue a conversation. Omit to start new. |
| `language` | string | ❌ | `en` or `hi` — Default: `en` |

**Example Request:**
```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "message": "Why are my money plant leaves turning yellow?",
    "session_id": "user_42_session"
  }'
```

**Response:**
```json
{
  "reply": "Yellow leaves on your Money Plant (Pothos) are usually caused by overwatering — the most common issue in Indian homes during monsoon season. Check if the soil is staying wet for more than 3-4 days. Let it dry out completely before the next watering. Also ensure the pot has drainage holes.\n\nDo you notice any yellowing pattern — older leaves at the bottom, or newer leaves at the top?",
  "session_id": "user_42_session",
  "suggested_products": null,
  "follow_up_questions": [
    "Are the yellowing leaves at the bottom or the top of the plant?",
    "How often are you currently watering it?"
  ]
}
```

---

### `GET /chat/history/{session_id}`

Retrieve full conversation history for a session.

**Example:**
```bash
curl http://localhost:8002/chat/history/user_42_session \
  -H "X-Api-Key: your_key"
```

**Response:**
```json
{
  "session_id": "user_42_session",
  "messages": [
    { "role": "user", "content": "Why are my money plant leaves turning yellow?" },
    { "role": "assistant", "content": "Yellow leaves on your Money Plant..." }
  ],
  "total_messages": 2
}
```

---

### `DELETE /chat/history/{session_id}`

Clear a user's chat session.

```json
{ "message": "Session cleared", "session_id": "user_42_session" }
```

---

## 5. Plant Doctor Service

**Direct port:** `8003`  
**Gateway path:** `/api/plant-diagnosis`

Diagnose plant diseases from images and/or symptoms using Claude Vision + Plant.id API.

---

### `POST /plant-diagnosis`

Analyze plant health. Provide an image (base64 or URL) and/or describe symptoms.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_base64` | string | ❌* | Base64-encoded image (JPEG/PNG/WebP) |
| `image_url` | string | ❌* | Public URL of the plant image |
| `symptoms` | string | ❌* | Text description of symptoms |
| `plant_name` | string | ❌ | Plant name to help diagnosis |

> *At least one of `image_base64`, `image_url`, or `symptoms` must be provided.

**Example Request (symptoms only):**
```bash
curl -X POST http://localhost:8003/plant-diagnosis \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "symptoms": "Brown spots on leaves, yellowing at edges, soil feels wet",
    "plant_name": "Snake Plant"
  }'
```

**Example Request (with image URL):**
```bash
curl -X POST http://localhost:8003/plant-diagnosis \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "image_url": "https://your-s3-bucket.s3.ap-south-1.amazonaws.com/plants/photo.jpg",
    "plant_name": "Snake Plant"
  }'
```

**Response:**
```json
{
  "plant_name": "Snake Plant (Sansevieria)",
  "diagnosis": [
    {
      "condition": "Root Rot",
      "severity": "high",
      "confidence": 0.87,
      "description": "Fungal infection caused by overwatering. Roots turn brown/black and mushy.",
      "causes": [
        "Overwatering — soil staying wet too long",
        "Poor drainage in the pot",
        "High humidity during monsoon"
      ],
      "solutions": [
        "Remove plant from pot immediately, trim black/mushy roots",
        "Let roots air dry for 30 minutes",
        "Repot in fresh, well-draining soil mix (50% cocopeat + 50% perlite)",
        "Apply copper fungicide available at local nurseries"
      ],
      "preventive_measures": [
        "Water only when top 2 inches of soil are completely dry",
        "Use pots with drainage holes"
      ],
      "products_recommended": [
        "Neem oil spray",
        "Copper oxychloride fungicide",
        "Well-draining cactus/succulent mix"
      ],
      "vet_consultation_needed": false
    }
  ],
  "overall_health_score": 0.35,
  "immediate_action": "Remove from pot NOW and inspect roots. Trim all black mushy roots with sterilised scissors.",
  "long_term_care": "Water Sansevieria only once every 2-3 weeks. It thrives on neglect — less water is always better."
}
```

**Severity Levels:**

| Value | Meaning |
|-------|---------|
| `low` | Minor issue, monitor the plant |
| `medium` | Needs treatment soon |
| `high` | Urgent action required |
| `critical` | Plant may die without immediate intervention |

---

## 6. SEO Content Service

**Direct port:** `8004`  
**Gateway path:** `/api/seo/generate-content`

Generate SEO-optimized content for plant product pages, blogs, meta tags, and FAQs using Claude Haiku.

---

### `POST /generate-content`

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `plant_name` | string | ✅ | Name of the plant |
| `type` | string | ✅ | Content type (see below) |
| `keywords` | array | ❌ | SEO keywords to include |
| `tone` | string | ❌ | `informative` \| `friendly` \| `professional` — Default: `informative` |
| `word_count` | integer | ❌ | Target word count — Default: `300` |

**Content Types (`type` field):**

| Value | Description |
|-------|-------------|
| `seo_description` | Product page description with meta tags |
| `blog_post` | Full blog article in markdown |
| `care_instructions` | Detailed care guide |
| `faq` | 8 Q&A pairs for the plant |
| `meta_tags` | Title, description, OG tags only |
| `product_title` | 5 SEO title variations |

**Example Request:**
```bash
curl -X POST http://localhost:8004/generate-content \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "plant_name": "Snake Plant",
    "type": "seo_description",
    "keywords": ["indoor plant", "air purifier", "low maintenance", "buy online India"],
    "tone": "friendly",
    "word_count": 200
  }'
```

**Response:**
```json
{
  "plant_name": "Snake Plant",
  "content_type": "seo_description",
  "content": "Bring home the ultimate indoor plant that practically takes care of itself! The Snake Plant (Sansevieria) is NASA's top-rated air purifier, removing toxins like formaldehyde and benzene from your home 24/7...",
  "meta_tags": {
    "title": "Buy Snake Plant Online India | Air Purifying Indoor Plant | PlantAtHome",
    "description": "Order Snake Plant online in India. NASA-certified air purifier, thrives in low light, perfect for beginners. Free delivery across India. Shop now at PlantAtHome.",
    "keywords": ["snake plant online", "sansevieria india", "air purifying plant", "indoor plant buy", "low maintenance plant"],
    "og_title": "Snake Plant — India's Favourite Air Purifier | PlantAtHome",
    "og_description": "NASA's top air-purifying plant delivered to your door. Perfect for bedrooms, offices & low-light spaces."
  },
  "word_count": 198,
  "seo_score": 0.88
}
```

> **Note:** Responses are cached in Redis for 24 hours. Same request returns instantly on repeat calls.

---

## 7. Semantic Search Service

**Direct port:** `8005`  
**Gateway path:** `/api/search`

Natural language plant search using Elasticsearch 8 kNN vector search (Sentence Transformers embeddings) + Claude AI reranking.

---

### `POST /search`

Search the plant catalog using natural language.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | ✅ | Natural language search query |
| `top_k` | integer | ❌ | Number of results — Default: `5`, Max: `20` |
| `filters` | object | ❌ | Optional filters (see below) |

**Available Filters:**

| Filter | Type | Description |
|--------|------|-------------|
| `max_price` | float | Maximum price in INR |
| `pet_friendly` | boolean | Filter for pet-safe plants only |
| `category` | string | `indoor` \| `outdoor` |
| `sunlight` | string | `low` \| `medium` \| `high` |
| `maintenance` | string | `low` \| `medium` \| `high` |

**Example Requests:**
```bash
# Natural language search
curl -X POST http://localhost:8005/search \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "query": "low maintenance plants for my dark bedroom under 500 rupees",
    "top_k": 5
  }'

# With filters
curl -X POST http://localhost:8005/search \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "query": "pet friendly plants",
    "top_k": 5,
    "filters": {
      "pet_friendly": true,
      "max_price": 800
    }
  }'
```

**Response:**
```json
{
  "query": "low maintenance plants for my dark bedroom under 500 rupees",
  "interpreted_query": "Low-light, easy-care indoor plants for bedroom with budget under ₹500",
  "results": [
    {
      "plant": {
        "id": "p001",
        "name": "Snake Plant (Sansevieria)",
        "description": "NASA-certified air purifier, nearly indestructible, perfect for beginners",
        "category": "indoor",
        "price": 299.0,
        "tags": ["air purifier", "bedroom", "low light"],
        "sunlight": "low",
        "maintenance": "low",
        "pet_friendly": false
      },
      "score": 0.94,
      "match_reason": "Perfect match — thrives in low/no light, requires watering only once a week, priced at ₹299"
    }
  ],
  "total": 5
}
```

---

### `POST /index`

Add a new plant to the search index (called from Laravel when a new product is created).

**Request Body:** Plant object

```bash
curl -X POST http://localhost:8005/index \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "id": "p100",
    "name": "Fiddle Leaf Fig",
    "description": "Trendy statement plant with large, violin-shaped leaves",
    "category": "indoor",
    "price": 1299.0,
    "tags": ["trendy", "statement", "large leaves", "instagram"],
    "sunlight": "medium",
    "maintenance": "high",
    "pet_friendly": false
  }'
```

**Response:**
```json
{
  "message": "Plant 'Fiddle Leaf Fig' indexed successfully",
  "plant_id": "p100",
  "total_indexed": 13
}
```

---

## 8. Notification Service

**Direct port:** `8006`  
**Gateway path:** `/api/notify`

Multi-channel notifications — Email (SMTP), WhatsApp (Meta Business API), SMS (Twilio), Push (Firebase FCM). Also consumes jobs from RabbitMQ queue `plantathome.notifications`.

---

### `POST /notify`

Send a single notification.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `channel` | string | ✅ | `email` \| `whatsapp` \| `sms` \| `push` |
| `type` | string | ✅ | Notification type (see below) |
| `recipient` | string | ✅ | Email / phone number / device token |
| `data` | object | ❌ | Template variables |
| `subject` | string | ❌ | Email subject override |

**Notification Types (`type` field):**

| Value | Template Variables |
|-------|-------------------|
| `order_placed` | `order_id`, `customer_name`, `plant_name` |
| `order_shipped` | `order_id`, `customer_name`, `plant_name`, `tracking_id`, `delivery_date` |
| `order_delivered` | `order_id`, `customer_name`, `plant_name` |
| `watering_reminder` | `plant_name`, `days_since_watering` |
| `fertilizer_reminder` | `plant_name` |
| `seasonal_care` | `season`, `care_message`, `customer_name` |
| `custom` | `subject`, `message` |

**Example — WhatsApp order confirmation:**
```bash
curl -X POST http://localhost:8006/notify \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "channel": "whatsapp",
    "type": "order_placed",
    "recipient": "+919876543210",
    "data": {
      "customer_name": "Rahul",
      "order_id": "ORD-2024-001",
      "plant_name": "Snake Plant"
    }
  }'
```

**Example — Email watering reminder:**
```bash
curl -X POST http://localhost:8006/notify \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "channel": "email",
    "type": "watering_reminder",
    "recipient": "customer@example.com",
    "data": {
      "plant_name": "Money Plant",
      "days_since_watering": 8
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "channel": "whatsapp",
  "recipient": "+919876543210",
  "message_id": "wamid.HBgLOTE5ODc2NTQz..."
}
```

---

### `POST /notify/bulk`

Send multiple notifications in one request.

**Request Body:**
```json
{
  "notifications": [
    {
      "channel": "sms",
      "type": "watering_reminder",
      "recipient": "+919876543210",
      "data": { "plant_name": "Snake Plant", "days_since_watering": 7 }
    },
    {
      "channel": "push",
      "type": "watering_reminder",
      "recipient": "fcm_device_token_here",
      "data": { "plant_name": "Peace Lily", "days_since_watering": 5 }
    }
  ]
}
```

**Response:**
```json
{
  "total": 2,
  "succeeded": 2,
  "failed": 0,
  "results": [
    { "success": true, "channel": "sms", "recipient": "+919876543210", "message_id": "SMxxxx" },
    { "success": true, "channel": "push", "recipient": "fcm_device_token_here", "message_id": "projects/..." }
  ]
}
```

---

## 9. Media Processing Service

**Direct port:** `8007`  
**Gateway path:** `/api/media/`

Image optimization, WebP conversion, thumbnail generation, AI background removal (rembg), S3 upload.

---

### `POST /process/image`

Optimize an image — resize, convert to WebP, optionally remove background and upload to S3.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_base64` | string | ✅ | Base64-encoded image |
| `output_format` | string | ❌ | `jpeg` \| `png` \| `webp` — Default: `webp` |
| `max_width` | integer | ❌ | Max width in px — Default: `1200` |
| `max_height` | integer | ❌ | Max height in px — Default: `1200` |
| `quality` | integer | ❌ | Compression quality 1–100 — Default: `85` |
| `remove_background` | boolean | ❌ | AI background removal — Default: `false` |
| `upload_to_s3` | boolean | ❌ | Upload result to S3 — Default: `false` |
| `s3_key` | string | ❌ | S3 object key (e.g. `products/snake-plant.webp`) |

**Example Request:**
```bash
curl -X POST http://localhost:8007/process/image \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "image_base64": "/9j/4AAQSkZJRgAB...",
    "output_format": "webp",
    "max_width": 800,
    "quality": 85,
    "remove_background": true,
    "upload_to_s3": true,
    "s3_key": "products/snake-plant-hero.webp"
  }'
```

**Response:**
```json
{
  "original_size_kb": 245.8,
  "processed_size_kb": 42.3,
  "compression_ratio": 5.81,
  "width": 800,
  "height": 600,
  "format": "webp",
  "image_base64": null,
  "s3_url": "https://plantathome-images.s3.ap-south-1.amazonaws.com/products/snake-plant-hero.webp"
}
```

---

### `POST /process/thumbnails`

Generate multiple thumbnail sizes from a single image.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image_base64` | string | ✅ | Base64-encoded image |
| `sizes` | array | ❌ | List of max sizes in px — Default: `[150, 300, 600]` |
| `output_format` | string | ❌ | `jpeg` \| `png` \| `webp` — Default: `webp` |
| `upload_to_s3` | boolean | ❌ | Default: `false` |
| `s3_prefix` | string | ❌ | S3 folder prefix (e.g. `thumbnails/snake-plant`) |

**Example Request:**
```bash
curl -X POST http://localhost:8007/process/thumbnails \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "image_base64": "/9j/4AAQSkZJRgAB...",
    "sizes": [150, 300, 600],
    "output_format": "webp",
    "upload_to_s3": true,
    "s3_prefix": "thumbnails/snake-plant"
  }'
```

**Response:**
```json
{
  "thumbnails": [
    { "size": 150, "image_base64": null, "s3_url": "https://...thumbnails/snake-plant/150.webp", "file_size_kb": 4.2 },
    { "size": 300, "image_base64": null, "s3_url": "https://...thumbnails/snake-plant/300.webp", "file_size_kb": 12.7 },
    { "size": 600, "image_base64": null, "s3_url": "https://...thumbnails/snake-plant/600.webp", "file_size_kb": 32.1 }
  ]
}
```

---

## 10. Analytics Service

**Direct port:** `8008`  
**Gateway path:** `/api/analytics/`

Track user events and query aggregated analytics — trending plants, search behavior, recommendation performance.

---

### `POST /events`

Track a user event.

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | ✅ | Event type (see below) |
| `user_id` | string | ❌ | Authenticated user ID |
| `session_id` | string | ❌ | Anonymous session ID |
| `plant_id` | string | ❌ | Plant involved in the event |
| `plant_name` | string | ❌ | Plant name |
| `query` | string | ❌ | Search query (for `search` events) |
| `metadata` | object | ❌ | Additional data |

**Event Types:**

| Value | When to fire | Key metadata fields |
|-------|-------------|-------------------|
| `search` | User performs a search | `results_count` |
| `plant_view` | User views a plant page | — |
| `recommendation_click` | User clicks a recommended plant | `recommendation_id` |
| `add_to_cart` | User adds plant to cart | `quantity`, `price` |
| `purchase` | Order completed | `order_id`, `amount` |
| `chatbot_query` | User sends chatbot message | — |
| `diagnosis_request` | User submits plant doctor request | — |

**Example:**
```bash
curl -X POST http://localhost:8008/events \
  -H "Content-Type: application/json" \
  -H "X-Api-Key: your_key" \
  -d '{
    "event_type": "search",
    "session_id": "sess_abc123",
    "query": "low maintenance plants for bedroom",
    "metadata": { "results_count": 5 }
  }'
```

**Response:**
```json
{ "event_id": "abc123xyz", "status": "tracked" }
```

---

### `GET /analytics/summary`

Get a full analytics summary.

**Query Parameters:**

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `days` | integer | `7` | Lookback period (1–90 days) |

```bash
curl "http://localhost:8008/analytics/summary?days=7" \
  -H "X-Api-Key: your_key"
```

**Response:**
```json
{
  "period": "last_7_days",
  "total_events": 1482,
  "trending_plants": [
    {
      "plant_id": "p001",
      "plant_name": "Snake Plant",
      "view_count": 312,
      "search_appearances": 87,
      "cart_adds": 54,
      "trend_score": 0.924
    }
  ],
  "popular_searches": [
    { "query": "low maintenance indoor plant", "count": 94, "avg_results": 5.0 },
    { "query": "pet friendly plants", "count": 67, "avg_results": 4.2 }
  ],
  "recommendation_performance": {
    "total_recommendations": 203,
    "total_clicks": 47,
    "click_through_rate": 0.2315,
    "top_recommended_plants": ["Snake Plant", "Money Plant", "ZZ Plant"]
  }
}
```

---

### `GET /analytics/trending`

Get trending plants only.

```bash
curl "http://localhost:8008/analytics/trending?days=7&limit=10" \
  -H "X-Api-Key: your_key"
```

---

### `GET /analytics/searches`

Get popular search queries.

```bash
curl "http://localhost:8008/analytics/searches?days=7" \
  -H "X-Api-Key: your_key"
```

---

## 11. Laravel Integration Reference

Add to `config/services.php`:
```php
'ai' => [
    'key'              => env('SERVICE_API_KEY'),
    'recommendation'   => env('RECOMMENDATION_SERVICE_URL', 'http://localhost:8001'),
    'chatbot'          => env('CHATBOT_SERVICE_URL',        'http://localhost:8002'),
    'plant_doctor'     => env('PLANT_DOCTOR_SERVICE_URL',   'http://localhost:8003'),
    'seo'              => env('SEO_SERVICE_URL',             'http://localhost:8004'),
    'search'           => env('SEMANTIC_SEARCH_SERVICE_URL', 'http://localhost:8005'),
    'notify'           => env('NOTIFICATION_SERVICE_URL',    'http://localhost:8006'),
    'media'            => env('MEDIA_SERVICE_URL',           'http://localhost:8007'),
    'analytics'        => env('ANALYTICS_SERVICE_URL',       'http://localhost:8008'),
],
```

Create a reusable helper in `App\Services\AiGateway.php`:
```php
<?php
namespace App\Services;

use Illuminate\Support\Facades\Http;

class AiGateway
{
    private string $key;

    public function __construct()
    {
        $this->key = config('services.ai.key');
    }

    private function headers(): array
    {
        return ['X-Api-Key' => $this->key, 'Accept' => 'application/json'];
    }

    public function recommend(array $params): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(60)
            ->post(config('services.ai.recommendation') . '/recommendations', $params)
            ->json();
    }

    public function chat(string $message, ?string $sessionId = null): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(60)
            ->post(config('services.ai.chatbot') . '/chat', [
                'message'    => $message,
                'session_id' => $sessionId ?? auth()->id() . '_' . session()->getId(),
            ])
            ->json();
    }

    public function diagnose(array $params): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(90)
            ->post(config('services.ai.plant_doctor') . '/plant-diagnosis', $params)
            ->json();
    }

    public function generateSeo(string $plantName, string $type, array $keywords = []): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(60)
            ->post(config('services.ai.seo') . '/generate-content', [
                'plant_name' => $plantName,
                'type'       => $type,
                'keywords'   => $keywords,
            ])
            ->json();
    }

    public function search(string $query, int $topK = 5, array $filters = []): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(30)
            ->post(config('services.ai.search') . '/search', [
                'query'   => $query,
                'top_k'   => $topK,
                'filters' => $filters ?: null,
            ])
            ->json();
    }

    public function notify(string $channel, string $type, string $recipient, array $data = []): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(30)
            ->post(config('services.ai.notify') . '/notify', [
                'channel'   => $channel,
                'type'      => $type,
                'recipient' => $recipient,
                'data'      => $data,
            ])
            ->json();
    }

    public function processImage(string $base64, array $options = []): array
    {
        return Http::withHeaders($this->headers())
            ->timeout(120)
            ->post(config('services.ai.media') . '/process/image', array_merge(
                ['image_base64' => $base64],
                $options
            ))
            ->json();
    }

    public function trackEvent(string $eventType, array $data = []): void
    {
        Http::withHeaders($this->headers())
            ->timeout(5)
            ->post(config('services.ai.analytics') . '/events', array_merge(
                ['event_type' => $eventType],
                $data
            ));
    }
}
```

---

## 12. RabbitMQ Queue Schema

Laravel can dispatch notification jobs directly to RabbitMQ. The notification service consumer picks them up automatically.

**Queue name:** `plantathome.notifications`  
**Exchange:** default (direct)  
**Message format:** JSON matching `NotificationRequest` schema

**Example Laravel dispatch:**
```php
// In your Order Observer, Job, or Event Listener
use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

$connection = new AMQPStreamConnection(
    env('RABBITMQ_HOST', 'localhost'), 5672,
    env('RABBITMQ_USER'), env('RABBITMQ_PASS')
);
$channel = $connection->channel();
$channel->queue_declare('plantathome.notifications', false, true, false, false);

$payload = json_encode([
    'channel'   => 'whatsapp',
    'type'      => 'order_placed',
    'recipient' => $order->customer_phone,
    'data'      => [
        'customer_name' => $order->customer_name,
        'order_id'      => $order->id,
        'plant_name'    => $order->plant_name,
    ],
]);

$msg = new AMQPMessage($payload, ['delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT]);
$channel->basic_publish($msg, '', 'plantathome.notifications');
$channel->close();
$connection->close();
```

---

## Swagger UI (Development)

Each service exposes interactive API docs at `/docs`:

| Service | Swagger URL |
|---------|-------------|
| Recommendation | `http://localhost:8001/docs` |
| Chatbot | `http://localhost:8002/docs` |
| Plant Doctor | `http://localhost:8003/docs` |
| SEO Content | `http://localhost:8004/docs` |
| Semantic Search | `http://localhost:8005/docs` |
| Notification | `http://localhost:8006/docs` |
| Media Processing | `http://localhost:8007/docs` |
| Analytics | `http://localhost:8008/docs` |

Via nginx gateway: `http://localhost/docs/{service}/`

---

*PlantAtHome AI Microservices — built with FastAPI, Claude AI, Elasticsearch, RabbitMQ*
