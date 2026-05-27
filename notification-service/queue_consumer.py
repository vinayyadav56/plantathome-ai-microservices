"""
RabbitMQ consumer — runs as a background task inside the FastAPI lifespan.
Laravel publishes notification jobs to the 'plantathome.notifications' queue.
This consumer picks them up and dispatches via the appropriate channel.
"""
import asyncio
import json
import logging
import os
import aio_pika
from models import NotificationRequest, NotificationChannel

logger = logging.getLogger("queue_consumer")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "plantathome.notifications"


async def _dispatch(request: NotificationRequest) -> None:
    from email_service import send_email
    from whatsapp_service import send_whatsapp
    from sms_service import send_sms
    from push_service import send_push

    handlers = {
        NotificationChannel.email:     send_email,
        NotificationChannel.whatsapp:  send_whatsapp,
        NotificationChannel.sms:       send_sms,
        NotificationChannel.push:      send_push,
    }
    handler = handlers.get(request.channel)
    if handler:
        result = handler(request)
        if not result.success:
            logger.error("Notification failed: %s — %s", request.recipient, result.error)
        else:
            logger.info("Notification sent: %s → %s (%s)", request.type, request.recipient, result.message_id)


async def _process_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=True):
        try:
            body = json.loads(message.body.decode())
            request = NotificationRequest(**body)
            await _dispatch(request)
        except Exception as e:
            logger.error("Failed to process message: %s", str(e))


async def start_consumer() -> None:
    retries = 0
    while retries < 10:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=10)
                queue = await channel.declare_queue(QUEUE_NAME, durable=True)
                logger.info("RabbitMQ consumer started — listening on '%s'", QUEUE_NAME)
                await queue.consume(_process_message)
                await asyncio.Future()  # run forever
        except Exception as e:
            retries += 1
            wait = min(2 ** retries, 30)
            logger.warning("RabbitMQ connection failed (%s). Retrying in %ds...", str(e), wait)
            await asyncio.sleep(wait)
