import os
import json
import uuid
import firebase_admin
from firebase_admin import credentials, messaging
from models import NotificationRequest, NotificationResult, NotificationChannel, NotificationType

_firebase_initialized = False

PUSH_TITLES = {
    NotificationType.order_placed:       "Order Confirmed! 🌿",
    NotificationType.order_shipped:      "Order Shipped! 📦",
    NotificationType.order_delivered:    "Order Delivered! 🌱",
    NotificationType.watering_reminder:  "Time to Water! 💧",
    NotificationType.fertilizer_reminder:"Fertilizer Time! 🌿",
    NotificationType.seasonal_care:      "Plant Care Tip 🌸",
    NotificationType.custom:             "{subject}",
}

PUSH_BODIES = {
    NotificationType.order_placed:       "Your {plant_name} order #{order_id} is confirmed.",
    NotificationType.order_shipped:      "Your {plant_name} is on its way! Track: {tracking_id}",
    NotificationType.order_delivered:    "Your {plant_name} has arrived. Happy gardening!",
    NotificationType.watering_reminder:  "Your {plant_name} needs water today!",
    NotificationType.fertilizer_reminder:"Your {plant_name} needs fertilizer this week.",
    NotificationType.seasonal_care:      "{care_message}",
    NotificationType.custom:             "{message}",
}


def _init_firebase() -> bool:
    global _firebase_initialized
    if _firebase_initialized:
        return True
    creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON", "{}")
    try:
        creds_dict = json.loads(creds_json)
        if not creds_dict.get("type"):
            return False
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
        return True
    except Exception:
        return False


def send_push(request: NotificationRequest) -> NotificationResult:
    if not _init_firebase():
        return NotificationResult(
            success=False,
            channel=NotificationChannel.push,
            recipient=request.recipient,
            error="Firebase credentials not configured",
        )

    title_tmpl = PUSH_TITLES.get(request.type, "PlantAtHome")
    body_tmpl = PUSH_BODIES.get(request.type, "{message}")
    try:
        title = title_tmpl.format(**request.data)
        body = body_tmpl.format(**request.data)
    except KeyError:
        title, body = title_tmpl, body_tmpl

    try:
        msg = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            token=request.recipient,
            data={k: str(v) for k, v in request.data.items()},
        )
        msg_id = messaging.send(msg)
        return NotificationResult(
            success=True,
            channel=NotificationChannel.push,
            recipient=request.recipient,
            message_id=msg_id,
        )
    except Exception as e:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.push,
            recipient=request.recipient,
            error=str(e),
        )
