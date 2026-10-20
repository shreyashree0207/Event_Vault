
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from pydantic import BaseModel
from datetime import datetime

from database import SessionLocal
from models import Event, Seat, Booking, Ticket
from rabbitmq_publisher import publish_ticket_job
from redis_client import redis_client


router = APIRouter(
    prefix="/bookings",
    tags=["Bookings"]
)


# =========================================================
# DATABASE DEPENDENCY
# =========================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =========================================================
# REQUEST MODEL
# =========================================================

class BookingRequest(BaseModel):
    eventId: str
    seatCodes: list[str]
    sessionId: str | None = None


# =========================================================
# CREATE BOOKING
# POST /bookings
# =========================================================

@router.post("")
def create_booking(
    booking_data: BookingRequest,
    db: Session = Depends(get_db)
):
    try:
        # Reject empty or duplicate seat selections
        if not booking_data.seatCodes:
            raise HTTPException(
                status_code=400,
                detail="No seats selected"
            )

        if len(set(booking_data.seatCodes)) != len(
            booking_data.seatCodes
        ):
            raise HTTPException(
                status_code=400,
                detail="Duplicate seat selections are not allowed"
            )

        # Lock the event row to serialize booking updates
        event = (
            db.query(Event)
            .filter(Event.id == booking_data.eventId)
            .with_for_update()
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=404,
                detail="Event not found"
            )

        # Lock selected seat rows in PostgreSQL
        selected_seats = (
            db.query(Seat)
            .filter(
                Seat.event_id == booking_data.eventId,
                Seat.seat_number.in_(booking_data.seatCodes)
            )
            .order_by(Seat.id)
            .with_for_update()
            .all()
        )

        # Make sure every requested seat exists
        if len(selected_seats) != len(booking_data.seatCodes):
            raise HTTPException(
                status_code=404,
                detail="One or more seats were not found"
            )

        # Check seat availability after acquiring row locks
        unavailable_seats = [
            seat.seat_number
            for seat in selected_seats
            if seat.status.lower() != "available"
        ]

        if unavailable_seats:
            raise HTTPException(
                status_code=409,
                detail=(
                    "Seats already booked or unavailable: "
                    + ", ".join(unavailable_seats)
                )
            )

        # Verify Redis seat-lock ownership
        for seat in selected_seats:
            lock_key = (
                f"seat-lock:{booking_data.eventId}:"
                f"{seat.seat_number}"
            )

            lock_owner = redis_client.get(lock_key)

            if lock_owner is not None:
                if (
                    booking_data.sessionId is None
                    or lock_owner != booking_data.sessionId
                ):
                    raise HTTPException(
                        status_code=409,
                        detail=(
                            f"Seat {seat.seat_number} is temporarily "
                            "locked by another session."
                        )
                    )

            elif booking_data.sessionId is not None:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Seat {seat.seat_number} is not locked "
                        "by this session."
                    )
                )

        # Ensure the event's availability count is consistent
        if event.available_seats < len(selected_seats):
            raise HTTPException(
                status_code=409,
                detail="Not enough available seats remain"
            )

        # Mark seats as booked
        for seat in selected_seats:
            seat.status = "booked"

        # The current model stores one seat per booking.
        # Create one booking record for each selected seat.
        booking_time = datetime.now().isoformat()
        bookings = []

        for seat in selected_seats:
            booking = Booking(
                user_id=1,
                event_id=booking_data.eventId,
                seat_id=seat.id,
                status="confirmed",
                booking_date=booking_time
            )
            bookings.append(booking)

        db.add_all(bookings)

        event.available_seats -= len(selected_seats)

        # Commit all booking and seat changes together
        db.commit()

        # Refresh generated booking IDs
        for booking in bookings:
            db.refresh(booking)

    except HTTPException:
        db.rollback()
        raise

    except RedisError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Seat-lock service is unavailable. Please try again."
        )

    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while creating the booking."
        )

    # The booking is committed. Queue ticket jobs afterwards.
    # A RabbitMQ failure must not undo an already committed booking.
    ticket_queue_warnings = []

    for booking in bookings:
        try:
            publish_ticket_job(booking.id)
        except Exception as exc:
            warning = (
                f"Booking {booking.id} was saved, but its ticket "
                f"job could not be queued: {exc}"
            )
            print(f"WARNING: {warning}")
            ticket_queue_warnings.append(booking.id)

    # Calculate payment
    ticket_price = event.starting_price * len(selected_seats)
    service_fee = round(ticket_price * 0.12, 2)
    total_amount = round(ticket_price + service_fee, 2)

    # Keep the existing response fields and include all booking IDs
    return {
        "id": bookings[0].id,
        "bookingIds": [booking.id for booking in bookings],
        "userId": bookings[0].user_id,
        "eventId": event.id,
        "eventName": event.name,
        "eventDate": event.date,
        "venue": event.venue,
        "seats": [seat.seat_number for seat in selected_seats],
        "ticketPrice": ticket_price,
        "serviceFee": service_fee,
        "totalAmount": total_amount,
        "paymentStatus": "PAID",
        "bookingStatus": "CONFIRMED",
        "createdAt": booking_time,
        "ticketQueueWarnings": ticket_queue_warnings
    }


# =========================================================
# GET SINGLE BOOKING
# GET /bookings/{booking_id}
# =========================================================

@router.get("/{booking_id}")
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    event = (
        db.query(Event)
        .filter(Event.id == booking.event_id)
        .first()
    )

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    seat = (
        db.query(Seat)
        .filter(Seat.id == booking.seat_id)
        .first()
    )

    ticket_price = event.starting_price
    service_fee = round(ticket_price * 0.12, 2)
    total_amount = round(ticket_price + service_fee, 2)

    return {
        "id": booking.id,
        "userId": booking.user_id,
        "eventId": booking.event_id,
        "eventName": event.name,
        "eventDate": event.date,
        "venue": event.venue,
        "seats": [seat.seat_number] if seat else [],
        "ticketPrice": ticket_price,
        "serviceFee": service_fee,
        "totalAmount": total_amount,
        "paymentStatus": "PAID",
        "bookingStatus": booking.status.upper(),
        "createdAt": booking.booking_date
    }


# =========================================================
# GET TICKET STATUS
# GET /bookings/{booking_id}/ticket-status
# =========================================================

@router.get("/{booking_id}/ticket-status")
def get_ticket_status(
    booking_id: int,
    db: Session = Depends(get_db)
):
    booking = (
        db.query(Booking)
        .filter(Booking.id == booking_id)
        .first()
    )

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    ticket = (
        db.query(Ticket)
        .filter(Ticket.booking_id == booking_id)
        .first()
    )

    if not ticket:
        return {
            "bookingId": booking.id,
            "status": "PROCESSING",
            "message": "Your ticket is being generated"
        }

    return {
        "bookingId": booking.id,
        "status": "READY",
        "ticketId": ticket.id,
        "ticketCode": ticket.ticket_code,
        "message": "Ticket is ready"
    }
