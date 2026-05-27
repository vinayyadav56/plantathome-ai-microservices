import os
import uuid
import httpx
from models import NotificationRequest, NotificationResult, NotificationChannel, NotificationType

WHATSAPP_API_URL = os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v18.0")
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")

# WhatsApp message templates (must be pre-approved in Meta Business Manager)
WA_TEMPLATES = {
    NotificationType.order_placed: {
        "name": "order_confirmed",
        "language": "en",
        "params": ["customer_name", "order_id", "plant_name"],
    },
    NotificationType.order_shipped: {
        "name": "order_shipped",
        "language": "en",
        "params": ["customer_name", "plant_name", "tracking_id", "delivery_date"],
    },
    NotificationType.order_delivered: {
        "name": "order_delivered",
        "language": "en",
        "params": ["customer_name", "plant_name"],
    },
    NotificationType.watering_reminder: {
        "name": "watering_reminder",
        "language": "en",
        "params": ["plant_name", "days_since_watering"],
    },
    NotificationType.fertilizer_reminder: {
        "name": "fertilizer_reminder",
        "language": "en",
        "params": ["plant_name"],
    },
    NotificationType.seasonal_care: {
        "name": "seasonal_care_tips",
        "language": "en",
        "params": ["season", "care_message"],
    },
}

# Fallback text messages when template not configured
TEXT_FALLBACKS = {
    NotificationType.watering_reminder: "💧 Reminder: Your {plant_name} needs watering today! It's been {days_since_watering} days.",
    NotificationType.fertilizer_reminder: "🌿 Reminder: Time to fertilize your {plant_name} this week!",
    NotificationType.order_placed: "✅ Order #{order_id} confirmed! Your {plant_name} will be delivered in 3-5 days.",
    NotificationType.order_shipped: "📦 Your {plant_name} is shipped! Tracking: {tracking_id}",
    NotificationType.order_delivered: "🌱 Your {plant_name} has been delivered! Happy gardening!",
    NotificationType.custom: "{message}",
}


def _build_template_payload(request: NotificationRequest) -> dict:
    tmpl = WA_TEMPLATES.get(request.type)
    if not tmpl:
        return _build_text_payload(request)

    components = []
    param_values = [str(request.data.get(p, "")) for p in tmpl["params"]]
    if param_values:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": v} for v in param_values],
        })

    return {
        "messaging_product": "whatsapp",
        "to": request.recipient,
        "type": "template",
        "template": {
            "name": tmpl["name"],
            "language": {"code": tmpl["language"]},
            "components": components,
        },
    }


def _build_text_payload(request: NotificationRequest) -> dict:
    tmpl = TEXT_FALLBACKS.get(request.type, "{message}")
    try:
        body = tmpl.format(**request.data)
    except KeyError:
        body = tmpl

    return {
        "messaging_product": "whatsapp",
        "to": request.recipient,
        "type": "text",
        "text": {"body": body},
    }


def send_whatsapp(request: NotificationRequest) -> NotificationResult:
    if not PHONE_NUMBER_ID or not ACCESS_TOKEN:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.whatsapp,
            recipient=request.recipient,
            error="WhatsApp API credentials not configured",
        )

    payload = _build_template_payload(request)
    url = f"{WHATSAPP_API_URL}/{PHONE_NUMBER_ID}/messages"

    try:
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        msg_id = resp.json().get("messages", [{}])[0].get("id", str(uuid.uuid4()))
        return NotificationResult(
            success=True,
            channel=NotificationChannel.whatsapp,
            recipient=request.recipient,
            message_id=msg_id,
        )
    except Exception as e:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.whatsapp,
            recipient=request.recipient,
            error=str(e),
        )
