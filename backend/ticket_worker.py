
import json
import os
import sys
from datetime import datetime, timezone
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
from models import Booking, Event, Seat, Ticket
from ticket_storage import generate_ticket_pdf, store_ticket_pdf


QUEUE_NAME = "event_vault_ticket_jobs"


def create_ticket(booking_id: int) -> None:
    """Generate and persist one ticket for a confirmed booking."""
    db = SessionLocal()

    try:
        booking = (
            db.query(Booking)
            .filter(Booking.id == booking_id)
            .with_for_update()
            .first()
        )

        if booking is None:
            raise ValueError(f"Booking {booking_id} does not exist")
        if booking.status.lower() != "confirmed":
            raise ValueError(f"Booking {booking_id} is not confirmed")

        ticket = (
            db.query(Ticket)
            .filter(Ticket.booking_id == booking_id)
            .with_for_update()
            .first()
        )

        if ticket is None:
            raise ValueError(f"Ticket record for booking {booking_id} does not exist")
        if ticket.status.lower() == "valid" and ticket.object_key:
            print(f"Ticket already exists for booking {booking_id}; skipping duplicate.")
            return

        claimed = (
            db.query(Ticket)
            .filter(
                Ticket.id == ticket.id,
                Ticket.status.in_(["pending", "failed"]),
            )
            .update(
                {
                    Ticket.status: "generating",
                    Ticket.error_message: None,
                    Ticket.generation_started_at: datetime.now(
                        timezone.utc
                    ).isoformat(),
                },
                synchronize_session=False,
            )
        )
        if not claimed:
            db.rollback()
            print(f"Ticket generation already in progress for booking {booking_id}.")
            return
        ticket_id = ticket.id
        ticket_code = ticket.ticket_code
        event = db.query(Event).filter(Event.id == booking.event_id).first()
        seat = db.query(Seat).filter(Seat.id == booking.seat_id).first()
        if event is None or seat is None:
            raise ValueError(f"Event or seat for booking {booking_id} does not exist")

        db.commit()

        content = generate_ticket_pdf(
            ticket_code=ticket_code,
            booking_id=booking_id,
            event_name=event.name,
            event_date=event.date,
            venue=event.venue,
            seat_number=seat.seat_number,
        )
        object_key = store_ticket_pdf(ticket_code, content)

        db.query(Ticket).filter(Ticket.id == ticket_id).update(
            {
                Ticket.status: "valid",
                Ticket.object_key: object_key,
                Ticket.error_message: None,
            },
            synchronize_session=False,
        )
        db.commit()
        print(f"Ticket created successfully for booking {booking_id}.")

    except Exception as exc:
        db.rollback()
        ticket = (
            db.query(Ticket)
            .filter(Ticket.booking_id == booking_id)
            .first()
        )
        if ticket:
            ticket.status = "failed"
            ticket.error_message = str(exc)[:1000]
            db.commit()
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