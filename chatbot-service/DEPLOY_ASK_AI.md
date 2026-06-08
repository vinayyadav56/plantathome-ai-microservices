# Ask AI — go-live runbook

Everything is built and on staging. The feature is **OFF by default**
(`ai_chat_settings.enabled = false`) and stays invisible until the steps below
are done. One shared secret is used in three places — generate it once:

```sh
openssl rand -hex 24        # e.g. SHARED=91f5ed24...   (use the same value 3x)
```

## 1. Deploy this service to Railway (+ Redis)
From a terminal that can reach railway.app:

```sh
cd chatbot-service
railway init                 # or `railway link` into the existing project
# In the Railway dashboard set this service's Root Directory = chatbot-service
railway add                  # add the Redis plugin  -> injects REDIS_URL
railway up                   # builds the Dockerfile
```

Set these service variables (dashboard or `railway variables set K=V`):

| var | value |
|-----|-------|
| `OPENAI_API_KEY` | the project OpenAI key (same one Plant Doctor uses) |
| `OPENAI_MODEL` | `gpt-4o-mini` |
| `REDIS_URL` | (auto from the Redis plugin) |
| `SERVICE_API_KEY` | `$SHARED` |
| `PERSIST_URL` | `https://<staging-api>/api/ai-chat/persist` (prod: `https://api.plantathome.in/api/ai-chat/persist`) |
| `PERSIST_KEY` | `$SHARED` |
| `CORS_ORIGINS` | `https://plantathome-shop-staging.vercel.app` (add the prod shop origin too) |

Grab the service URL, e.g. `https://plantathome-chatbot-production.up.railway.app`.
Sanity: `curl $URL/health` → `{"status":"ok","redis":"ok"}`.

## 2. Wire the shop (Vercel env)
On the shop project (staging, then prod):

| var | value |
|-----|-------|
| `CHATBOT_SERVICE_URL` | the Railway service URL from step 1 |
| `CHATBOT_SERVICE_API_KEY` | `$SHARED` |

Redeploy the shop so the serverless proxy picks up the env.

## 3. Wire the API (Railway env)
On the API service (staging, then prod):

| var | value |
|-----|-------|
| `AI_CHAT_SERVICE_API_KEY` | `$SHARED` |

(Used to verify the service's transcript-persist callback. Must equal `PERSIST_KEY`.)

## 4. Turn it on
Admin → **Tools → Ask AI Chats → Feature Control** → toggle **enabled** → Save.
(Optionally paste the service URL there for reference; the cap/model/budget too.)

The "✨ Ask AI" tag now appears on every plant card. Logged-in users get a
plant-scoped chat (10 Q's/chat), transcripts land under **Ask AI Chats →
Conversations** by user id with date/time + token cost.

## Prod note
The marvel package changed, so prod needs the usual
`gh workflow run prod-data-op.yml -f mode=... ` **composer reinstall** path (same
gotcha as Plant Doctor/SKUs), plus `AI_CHAT_SERVICE_API_KEY` on the prod API and
`CHATBOT_SERVICE_*` on the prod shop. The migrations run automatically on deploy.
