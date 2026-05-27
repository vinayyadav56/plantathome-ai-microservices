import os
import uuid
import httpx
from models import NotificationRequest, NotificationResult, NotificationChannel, NotificationType

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM = os.getenv("TWILIO_SMS_FROM", "")

SMS_TEMPLATES = {
    NotificationType.order_placed:       "PlantAtHome: Order #{order_id} confirmed! Your {plant_name} will arrive in 3-5 days.",
    NotificationType.order_shipped:      "PlantAtHome: Your {plant_name} is shipped! Track: {tracking_id}",
    NotificationType.order_delivered:    "PlantAtHome: Your {plant_name} is delivered! Water it within 24 hrs. Happy gardening!",
    NotificationType.watering_reminder:  "PlantAtHome Reminder: Water your {plant_name} today! {days_since_watering} days since last watering.",
    NotificationType.fertilizer_reminder:"PlantAtHome Reminder: Time to fertilize your {plant_name}!",
    NotificationType.seasonal_care:      "PlantAtHome: {season} care tip — {care_message}",
    NotificationType.custom:             "{message}",
}


def send_sms(request: NotificationRequest) -> NotificationResult:
    if not TWILIO_SID or not TWILIO_TOKEN or not TWILIO_FROM:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.sms,
            recipient=request.recipient,
            error="Twilio SMS credentials not configured",
        )

    tmpl = SMS_TEMPLATES.get(request.type, "{message}")
    try:
        body = tmpl.format(**request.data)
    except KeyError:
        body = tmpl

    try:
        resp = httpx.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json",
            auth=(TWILIO_SID, TWILIO_TOKEN),
            data={"From": TWILIO_FROM, "To": request.recipient, "Body": body},
            timeout=10,
        )
        resp.raise_for_status()
        return NotificationResult(
            success=True,
            channel=NotificationChannel.sms,
            recipient=request.recipient,
            message_id=resp.json().get("sid", str(uuid.uuid4())),
        )
    except Exception as e:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.sms,
            recipient=request.recipient,
            error=str(e),
        )
