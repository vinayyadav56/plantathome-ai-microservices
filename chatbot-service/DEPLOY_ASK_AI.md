# Ask AI — go-live runbook

Everything is built and on staging. The feature is **OFF by default**
(`ai_chat_settings.enabled = false`) and stays invisible until the steps below are done.

One **shared secret** is used in a few places — pick it once and reuse it:
```
SHARED = 91f5ed24e4be44ca7fb7a02b577b8ac8c6695635d3605157     # or: openssl rand -hex 24
```

## 1. Create the chatbot service in Railway (mirrors plant-doctor)
This is the same pattern as your other services: a service in the **`plantathome-staging`**
project, connected to GitHub, that **auto-deploys on push**. In the Railway dashboard:

1. **plantathome-staging** project → **New → Deploy from GitHub repo** →
   `vinayyadav56/plantathome-ai-microservices`
   → **Settings → Root Directory = `chatbot-service`**, branch `main`.
   (Railway builds `chatbot-service/Dockerfile` and redeploys on every push.)
2. **New → Database → Redis** (same project).
3. The chatbot service → **Variables**:

   | var | value |
   |-----|-------|
   | `OPENAI_API_KEY` | copy from the existing **plant-doctor** service's variables |
   | `OPENAI_MODEL` | `gpt-4o-mini` |
   | `SERVICE_API_KEY` | `$SHARED` |
   | `PERSIST_KEY` | `$SHARED` |
   | `PERSIST_URL` | `https://plantathome-production.up.railway.app/api/ai-chat/persist` |
   | `CORS_ORIGINS` | `https://plantathome-shop-staging.vercel.app` |
   | `REDIS_URL` | reference the Redis plugin: `${{Redis.REDIS_URL}}` |

4. Service → **Settings → Networking → Generate Domain** → copy the URL
   (e.g. `https://chatbot-service-production.up.railway.app`).
   Sanity: `curl $URL/health` → `{"status":"ok","redis":"ok"}`.

## 2. Add ONE variable to the API service
On the **API** service in the same Railway project → **Variables**:

| var | value |
|-----|-------|
| `AI_CHAT_SERVICE_API_KEY` | `$SHARED` |

(Authenticates the service's transcript-persist callback into Laravel. Must equal `PERSIST_KEY`.)

## 3. Shop env — I can do this for you
Tell me the service URL from step 1 and I'll set `CHATBOT_SERVICE_URL` + `CHATBOT_SERVICE_API_KEY`
on the shop via the shop repo's existing `VERCEL_TOKEN` and redeploy. (Or set them in the Vercel
dashboard yourself.)

## 4. Turn it on
Admin → **Tools → Ask AI Chats → Feature Control** → toggle **enabled** → Save.

The "✨ Ask AI" tag then appears on every plant card; logged-in users get a plant-scoped chat
(10 Q's/chat), and transcripts land under **Ask AI Chats → Conversations** by user id with
date/time + token cost.

---

### Alternative: CLI deploy (`railway up`)
If you'd rather not use the dashboard, from a terminal that can reach railway.app:
```sh
cd chatbot-service
railway link            # into the plantathome-staging project
railway up              # builds the Dockerfile
# then set the same variables as step 1, add Redis, generate a domain
```
(There's also a manual GitHub Actions fallback, `.github/workflows/deploy-chatbot.yml`, that runs
`railway up` from a runner using a `RAILWAY_TOKEN` project-token secret.)

### Prod later
Repeat in the prod Railway project + prod shop/API env. The marvel package changed, so prod also
needs the usual **composer reinstall** path (`gh workflow run prod-data-op.yml …`, same gotcha as
Plant Doctor/SKUs). Migrations run automatically on deploy.
