from pydantic import BaseModel, EmailStr
from typing import Optional
from enum import Enum


class NotificationChannel(str, Enum):
    email = "email"
    whatsapp = "whatsapp"
    sms = "sms"
    push = "push"


class NotificationType(str, Enum):
    order_placed = "order_placed"
    order_shipped = "order_shipped"
    order_delivered = "order_delivered"
    watering_reminder = "watering_reminder"
    fertilizer_reminder = "fertilizer_reminder"
    seasonal_care = "seasonal_care"
    custom = "custom"


class NotificationRequest(BaseModel):
    channel: NotificationChannel
    type: NotificationType
    recipient: str  # email / phone / device_token depending on channel
    data: dict = {}  # template variables (order_id, plant_name, etc.)
    subject: Optional[str] = None  # email subject override

    class Config:
        json_schema_extra = {
            "example": {
                "channel": "whatsapp",
                "type": "watering_reminder",
                "recipient": "+919876543210",
                "data": {"plant_name": "Snake Plant", "days_since_watering": 7}
            }
        }


class BulkNotificationRequest(BaseModel):
    notifications: list[NotificationRequest]


class NotificationResult(BaseModel):
    success: bool
    channel: NotificationChannel
    recipient: str
    message_id: Optional[str] = None
    error: Optional[str] = None


class BulkNotificationResponse(BaseModel):
    total: int
    succeeded: int
    failed: int
    results: list[NotificationResult]
