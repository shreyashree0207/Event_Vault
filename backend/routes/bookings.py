
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
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
    # Find event
    event = db.query(Event).filter(
        Event.id == booking_data.eventId
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Make sure at least one seat was selected
    if not booking_data.seatCodes:
        raise HTTPException(
            status_code=400,
            detail="No seats selected"
        )

    # Find selected seats
    selected_seats = db.query(Seat).filter(
        Seat.event_id == booking_data.eventId,
        Seat.seat_number.in_(booking_data.seatCodes)
    ).all()

    # Check that all requested seats exist
    if len(selected_seats) != len(booking_data.seatCodes):
        raise HTTPException(
            status_code=404,
            detail="One or more seats were not found"
        )

    # Check whether any seat is already booked
    unavailable_seats = [
        seat.seat_number
        for seat in selected_seats
        if seat.status != "available"
    ]

    if unavailable_seats:
        raise HTTPException(
            status_code=409,
            detail=f"Seats already booked: {', '.join(unavailable_seats)}"
        )

    # Check Redis locks before booking seats
    for seat in selected_seats:
        lock_key = f"seat-lock:{booking_data.eventId}:{seat.seat_number}"
        lock_owner = redis_client.get(lock_key)

        if lock_owner is not None and lock_owner != booking_data.sessionId:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Seat {seat.seat_number} is temporarily "
                    "locked by another session."
                )
            )

        if booking_data.sessionId is not None and lock_owner is None:
            raise HTTPException(
                status_code=409,
                detail=f"Seat {seat.seat_number} is not locked by this session."
            )

    # Mark selected seats as booked
    for seat in selected_seats:
        seat.status = "booked"

    # -----------------------------------------------------
    # CREATE BOOKING
    # -----------------------------------------------------
    #
    # Current database design has one seat_id.
    # Therefore, for now, we store the first selected seat.
    #
    booking = Booking(
        user_id=1,
        event_id=booking_data.eventId,
        seat_id=selected_seats[0].id,
        status="confirmed",
        booking_date=datetime.now().isoformat()
    )

    db.add(booking)

    # Update available seats
    event.available_seats = max(
        0,
        event.available_seats - len(selected_seats)
    )
    # Save the booking to PostgreSQL first
    db.commit()
    db.refresh(booking)

# Send a ticket-generation job to RabbitMQ
    try:
       publish_ticket_job(booking.id)
    except Exception as exc:
       print(
           f"WARNING: Booking {booking.id} was saved, "
           f"but its ticket job could not be queued: {exc}"
    )

    # -----------------------------------------------------
    # PAYMENT CALCULATION
    # -----------------------------------------------------

    ticket_price = (
        event.starting_price * len(selected_seats)
    )

    service_fee = round(
        ticket_price * 0.12,
        2
    )

    total_amount = round(
        ticket_price + service_fee,
        2
    )

    return {
        "id": booking.id,
        "userId": booking.user_id,
        "eventId": booking.event_id,

        "eventName": event.name,
        "eventDate": event.date,
        "venue": event.venue,

        "seats": booking_data.seatCodes,

        "ticketPrice": ticket_price,
        "serviceFee": service_fee,
        "totalAmount": total_amount,

        "paymentStatus": "PAID",
        "bookingStatus": "CONFIRMED",
        "createdAt": booking.booking_date
    }


# =========================================================
# GET USER BOOKINGS
# GET /user/bookings
# =========================================================
#
# IMPORTANT:
# This endpoint is intentionally NOT inside the bookings
# router because the router already has:
#
#     prefix="/bookings"
#
# Therefore putting /user/bookings here would create:
#
#     /bookings/user/bookings
#
# But the frontend needs:
#
#     /user/bookings
#
# So this endpoint is defined in main.py instead.
#
# =========================================================


# =========================================================
# GET SINGLE BOOKING
# GET /bookings/{booking_id}
# =========================================================

@router.get("/{booking_id}")
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db)
):
    # Find booking
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    # Find event
    event = db.query(Event).filter(
        Event.id == booking.event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Find seat stored for this booking
    seat = db.query(Seat).filter(
        Seat.id == booking.seat_id
    ).first()

    booked_seats = []

    if seat:
        booked_seats.append(
            seat.seat_number
        )

    # -----------------------------------------------------
    # PAYMENT CALCULATION
    # -----------------------------------------------------

    ticket_price = event.starting_price

    service_fee = round(
        ticket_price * 0.12,
        2
    )

    total_amount = round(
        ticket_price + service_fee,
        2
    )

    return {
        "id": booking.id,
        "userId": booking.user_id,
        "eventId": booking.event_id,

        "eventName": event.name,
        "eventDate": event.date,
        "venue": event.venue,

        "seats": booked_seats,

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
# GET TICKET STATUS
@router.get("/{booking_id}/ticket-status")
def get_ticket_status(
    booking_id: int,
    db: Session = Depends(get_db)
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()

    if not booking:
        raise HTTPException(
            status_code=404,
            detail="Booking not found"
        )

    ticket = db.query(Ticket).filter(
        Ticket.booking_id == booking_id
    ).first()

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

    # -----------------------------------------------------
    # TEMPORARY IMPLEMENTATION
    # -----------------------------------------------------
    #
    # Currently we directly return READY.
    #
    # Later this will become:
    #
    # Booking
    #     ↓
    # RabbitMQ
    #     ↓
    # Ticket Service
    #     ↓
    # Generate Ticket
    #     ↓
    # S3 / MinIO
    #
    # -----------------------------------------------------

    return {
        "bookingId": booking.id,
        "status": "READY",
        "message": "Ticket is ready"
    }