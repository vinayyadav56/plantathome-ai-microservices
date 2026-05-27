import os
import smtplib
import uuid
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from models import NotificationRequest, NotificationResult, NotificationChannel, NotificationType

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@plantathome.in")

EMAIL_TEMPLATES = {
    NotificationType.order_placed: {
        "subject": "Your PlantAtHome Order #{order_id} is Confirmed!",
        "body": """<h2>🌿 Order Confirmed!</h2>
<p>Hi {customer_name},</p>
<p>Your order <strong>#{order_id}</strong> has been placed successfully.</p>
<p>You ordered: <strong>{plant_name}</strong></p>
<p>We'll notify you when it's shipped. Expected delivery in 3-5 business days.</p>
<p>Thanks for choosing PlantAtHome!</p>""",
    },
    NotificationType.order_shipped: {
        "subject": "Your PlantAtHome Order #{order_id} is on the Way!",
        "body": """<h2>📦 Order Shipped!</h2>
<p>Hi {customer_name},</p>
<p>Your <strong>{plant_name}</strong> is on its way!</p>
<p>Tracking ID: <strong>{tracking_id}</strong></p>
<p>Expected delivery: <strong>{delivery_date}</strong></p>""",
    },
    NotificationType.order_delivered: {
        "subject": "Your PlantAtHome Order is Delivered!",
        "body": """<h2>🌱 Order Delivered!</h2>
<p>Hi {customer_name},</p>
<p>Your <strong>{plant_name}</strong> has been delivered!</p>
<p>Care tip: Water it within 24 hours of receiving. Keep it away from direct sunlight for the first 2 days.</p>
<p>Happy gardening!</p>""",
    },
    NotificationType.watering_reminder: {
        "subject": "Time to Water Your {plant_name}!",
        "body": """<h2>💧 Watering Reminder</h2>
<p>Hi there,</p>
<p>Your <strong>{plant_name}</strong> is due for watering today!</p>
<p>It's been <strong>{days_since_watering} days</strong> since the last watering.</p>
<p>Pro tip: Check the topsoil — if the top inch is dry, it's time to water.</p>""",
    },
    NotificationType.fertilizer_reminder: {
        "subject": "Time to Fertilize Your {plant_name}!",
        "body": """<h2>🌿 Fertilizer Reminder</h2>
<p>Your <strong>{plant_name}</strong> needs fertilizer this week.</p>
<p>Use a balanced NPK fertilizer diluted to half strength for best results.</p>""",
    },
    NotificationType.seasonal_care: {
        "subject": "Seasonal Plant Care Tips for {season}",
        "body": """<h2>🌸 {season} Plant Care Tips</h2>
<p>Hi {customer_name},</p>
<p>{care_message}</p>""",
    },
    NotificationType.custom: {
        "subject": "{subject}",
        "body": "{message}",
    },
}

HTML_WRAPPER = """<!DOCTYPE html>
<html><body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#333;">
<div style="background:#2d6a4f;padding:15px;border-radius:8px 8px 0 0;">
  <h1 style="color:white;margin:0;font-size:22px;">🌿 PlantAtHome</h1>
</div>
<div style="border:1px solid #ddd;border-top:none;padding:20px;border-radius:0 0 8px 8px;">
{content}
<hr style="border:none;border-top:1px solid #eee;margin:20px 0;">
<p style="color:#999;font-size:12px;">PlantAtHome | plantathome.in</p>
</div>
</html>"""


def _render(template: str, data: dict) -> str:
    try:
        return template.format(**data)
    except KeyError:
        return template


def send_email(request: NotificationRequest) -> NotificationResult:
    tmpl = EMAIL_TEMPLATES.get(request.type, EMAIL_TEMPLATES[NotificationType.custom])
    subject = _render(request.subject or tmpl["subject"], request.data)
    body_html = HTML_WRAPPER.format(content=_render(tmpl["body"], request.data))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = request.recipient
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, request.recipient, msg.as_string())
        return NotificationResult(
            success=True,
            channel=NotificationChannel.email,
            recipient=request.recipient,
            message_id=str(uuid.uuid4()),
        )
    except Exception as e:
        return NotificationResult(
            success=False,
            channel=NotificationChannel.email,
            recipient=request.recipient,
            error=str(e),
        )
