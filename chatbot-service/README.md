# Ask-AI Chatbot Service

Per-plant, topic-scoped AI chat for the PlantAtHome storefront. Async FastAPI +
Redis + OpenAI (`gpt-4o-mini`). Engineered for the chat hot path so Laravel/PHP-FPM
is only touched once per conversation (the transcript persist).

## Endpoints
- `GET  /health` — liveness + Redis ping.
- `POST /ask`  (X-Api-Key) — `{user_id, plant{id,name,scientific_name,facts}, message, conversation_id?, language}`
  → `{reply, conversation_id, prompt_count, limit_reached, usage{prompt_tokens,completion_tokens,model}}`.
  Enforces the 10-prompt cap (atomic), per-user daily cap, and per-user rate limit.
- `POST /end`  (X-Api-Key) — `{conversation_id}` → persists the transcript to Laravel once, drops live state.

A background sweeper flushes conversations idle for `IDLE_SECONDS` so abandoned
chats are still saved exactly once.

## Why it scales
Fully async + stateless. Live state and all guards live in Redis (O(1), TTL-GC).
MySQL sees ~1 write per conversation. Scale out = more Railway replicas sharing
Redis. An OpenAI concurrency semaphore degrades gracefully (localized "busy")
under spikes; a first-turn cross-user Q&A cache cuts cost/latency on popular plants.

## Env
| var | purpose |
|-----|---------|
| `OPENAI_API_KEY` | OpenAI key (reuse the project key) |
| `OPENAI_MODEL` | default `gpt-4o-mini` |
| `REDIS_URL` | Railway Redis URL |
| `SERVICE_API_KEY` | X-Api-Key the Laravel proxy must send to `/ask` and `/end` |
| `PERSIST_URL` | Laravel internal persist endpoint, e.g. `https://api.plantathome.in/api/ai-chat/persist` |
| `PERSIST_KEY` | X-Api-Key sent to the persist endpoint (matches `AI_CHAT_SERVICE_API_KEY` on the API) |
| `CORS_ORIGINS` | comma list of allowed origins (`*` for dev) |
| `MAX_PROMPTS` | prompts per chat, default `10` |
| `DAILY_USER_CAP` | prompts per user per day, default `60` |
| `MAX_REPLY_TOKENS` | reply cap, default `450` |

## Deploy (Railway)
```sh
railway init            # or: railway link  (existing project)
railway up              # builds the Dockerfile in this dir
railway add             # add the Redis plugin -> sets REDIS_URL
# then set the env vars above in the Railway dashboard / `railway variables set ...`
```
Point the service "Root Directory" at `chatbot-service/` (monorepo).
