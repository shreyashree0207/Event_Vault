
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from redis.exceptions import RedisError
from pydantic import BaseModel
from datetime import datetime
import uuid

from database import SessionLocal
from models import Event, Seat, Booking, Ticket
from rabbitmq_publisher import publish_ticket_job
from redis_client import redis_client
from auth import AuthenticatedUser, get_current_user
from waiting_room_store import release_admission, validate_admission_token


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
    admissionToken: str | None = None


# =========================================================
# CREATE BOOKING
# POST /bookings
# =========================================================

@router.post("")
def create_booking(
    booking_data: BookingRequest,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    try:
        if not booking_data.sessionId:
            raise HTTPException(
                status_code=400,
                detail="sessionId is required to confirm a booking"
            )
        if booking_data.sessionId != current_user.session_id:
            raise HTTPException(
                status_code=403,
                detail="Booking session does not belong to the signed-in user.",
            )
        if not booking_data.admissionToken or not validate_admission_token(
            booking_data.eventId,
            current_user.session_id,
            booking_data.admissionToken,
        ):
            raise HTTPException(
                status_code=403,
                detail="A valid waiting-room admission is required to book seats.",
            )

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
                user_id=current_user.id,
                event_id=booking_data.eventId,
                seat_id=seat.id,
                status="confirmed",
                booking_date=booking_time
            )
            bookings.append(booking)

        db.add_all(bookings)
        db.flush()

        db.add_all([
            Ticket(
                booking_id=booking.id,
                ticket_code=f"EV-{uuid.uuid4().hex.upper()}",
                status="pending",
                ticket_url=None,
                object_key=None,
                error_message=None,
                created_at=booking_time,
            )
            for booking in bookings
        ])

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
    admission_release_warning = False

    try:
        release_admission(
            booking_data.eventId,
            current_user.session_id,
            booking_data.admissionToken,
        )
    except RedisError as exc:
        admission_release_warning = True
        print(f"WARNING: Booking {bookings[0].id} completed but admission could not be released: {exc}")

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
        "ticketQueueWarnings": ticket_queue_warnings,
        "admissionReleaseWarning": admission_release_warning,
    }


# =========================================================
# GET SINGLE BOOKING
# GET /bookings/{booking_id}
# =========================================================

@router.get("/{booking_id}")
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
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
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    booking = (
        db.query(Booking)
        .filter(
            Booking.id == booking_id,
            Booking.user_id == current_user.id,
        )
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
        raise HTTPException(
            status_code=409,
            detail="Ticket generation has not been queued. Please retry ticket generation.",
        )

    return {
        "bookingId": booking.id,
        "status": (
            "READY" if ticket.status.lower() == "valid"
            else ticket.status.upper()
        ),
        "ticketId": ticket.id,
        "ticketCode": ticket.ticket_code,
        "message": (
            "Ticket is ready" if ticket.status.lower() == "valid"
            else (
                "Ticket generation failed. Retry generation from My Tickets."
                if ticket.status.lower() == "failed"
                else "Ticket generation is in progress."
            )
        ),
    }
