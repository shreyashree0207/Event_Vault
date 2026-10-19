import json
import os
import pika
from dotenv import load_dotenv
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

QUEUE_NAME = "event_vault_ticket_jobs"


def publish_ticket_job(booking_id: int) -> None:
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    username = os.getenv("RABBITMQ_USER")
    password = os.getenv("RABBITMQ_PASSWORD")

    if not username or not password:
        raise RuntimeError(
            "RABBITMQ_USER and RABBITMQ_PASSWORD must be set in backend/.env"
        )

    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(
        host=host,
        port=port,
        credentials=credentials,
        heartbeat=60,
        blocked_connection_timeout=30,
    )

    connection = pika.BlockingConnection(parameters)

    try:
        channel = connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        message = json.dumps({"booking_id": booking_id})

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=message.encode("utf-8"),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type="application/json",
            ),
            mandatory=True,
        )

        print(f"Ticket job published for booking {booking_id}.")
    finally:
        if connection.is_open:
            connection.close()