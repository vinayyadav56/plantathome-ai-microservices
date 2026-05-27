from dotenv import load_dotenv
load_dotenv()

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from models import (
    NotificationRequest, NotificationResult,
    BulkNotificationRequest, BulkNotificationResponse,
    NotificationChannel,
)
from email_service import send_email
from whatsapp_service import send_whatsapp
from sms_service import send_sms
from push_service import send_push
from queue_consumer import start_consumer
from auth import verify_api_key


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start RabbitMQ consumer in background
    asyncio.create_task(start_consumer())
    yield


app = FastAPI(
    title="PlantAtHome Notification Service",
    description="Multi-channel notifications — Email, WhatsApp, SMS, Push + RabbitMQ consumer",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CHANNEL_HANDLERS = {
    NotificationChannel.email:    send_email,
    NotificationChannel.whatsapp: send_whatsapp,
    NotificationChannel.sms:      send_sms,
    NotificationChannel.push:     send_push,
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "notification-service"}


@app.post("/notify", response_model=NotificationResult)
def send_notification(request: NotificationRequest, _: None = Depends(verify_api_key)):
    handler = CHANNEL_HANDLERS.get(request.channel)
    if not handler:
        raise HTTPException(status_code=400, detail=f"Unknown channel: {request.channel}")
    return handler(request)


@app.post("/notify/bulk", response_model=BulkNotificationResponse)
def send_bulk(request: BulkNotificationRequest, _: None = Depends(verify_api_key)):
    results = []
    for notif in request.notifications:
        handler = CHANNEL_HANDLERS.get(notif.channel)
        if handler:
            results.append(handler(notif))

    succeeded = sum(1 for r in results if r.success)
    return BulkNotificationResponse(
        total=len(results),
        succeeded=succeeded,
        failed=len(results) - succeeded,
        results=results,
    )
