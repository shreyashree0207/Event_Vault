
import json
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pika
from dotenv import load_dotenv
from sqlalchemy.exc import SQLAlchemyError

# Load the backend's private environment file.
BACKEND_DIR = Path(__file__).resolve().parent
load_dotenv(BACKEND_DIR / ".env")

# Allow imports from the backend directory.
sys.path.insert(0, str(BACKEND_DIR))

from database import SessionLocal
from models import Booking, Ticket


QUEUE_NAME = "event_vault_ticket_jobs"


def create_ticket(booking_id: int) -> None:
    """Create one ticket for a booking, without duplicating existing tickets."""
    db = SessionLocal()

    try:
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .first()
        )

        if booking is None:
            raise ValueError(f"Booking {booking_id} does not exist")

        existing_ticket = (
            db.query(Ticket)
            .filter(Ticket.booking_id == booking_id)
            .first()
        )

        if existing_ticket:
            print(
                f"Ticket already exists for booking {booking_id}; "
                "skipping duplicate."
            )
            return

        ticket = Ticket(
            booking_id=booking_id,
            ticket_code=f"EV-{booking_id}-{uuid.uuid4().hex[:8].upper()}",
            status="valid",
            ticket_url="#",
            created_at=datetime.now().isoformat(),
        )

        db.add(ticket)
        db.commit()

        print(f"Ticket created successfully for booking {booking_id}.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def main() -> None:
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
    channel = connection.channel()

    channel.queue_declare(
        queue=QUEUE_NAME,
        durable=True,
    )

    # Process one message at a time.
    channel.basic_qos(prefetch_count=1)

    def handle_message(ch, method, properties, body):
        try:
            message = json.loads(body.decode("utf-8"))
            booking_id = message.get("booking_id")

            if (
                not isinstance(booking_id, int)
                or isinstance(booking_id, bool)
                or booking_id <= 0
            ):
                raise ValueError("Message must contain a positive integer booking_id")

            create_ticket(booking_id)

        except ValueError as exc:
            # Invalid messages should not block the queue indefinitely.
            print(f"Rejecting invalid ticket job: {exc}")
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False,
            )

        except (SQLAlchemyError, pika.exceptions.AMQPError) as exc:
            # Retry transient database or messaging failures.
            print(f"Temporary processing error: {exc}")
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )

        except Exception as exc:
            # Keep unexpected failures visible and retry for now.
            print(f"Unexpected ticket worker error: {exc}")
            ch.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=True,
            )

        else:
            # Acknowledge only after ticket processing succeeds.
            ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=handle_message,
    )

    print(f"Ticket worker is listening on queue: {QUEUE_NAME}")
    print("Press Ctrl+C to stop.")

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\nStopping ticket worker...")
        if channel.is_open:
            channel.stop_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()