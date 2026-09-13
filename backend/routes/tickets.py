from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from database import SessionLocal
from models import Booking, Event, Seat, Ticket


router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
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
# GET ALL TICKETS FOR CURRENT USER
# GET /tickets
# =========================================================

@router.get("")
def get_tickets(
    db: Session = Depends(get_db)
):
    # -----------------------------------------------------
    # TEMPORARY USER
    # -----------------------------------------------------
    #
    # Authentication is not implemented yet.
    # Therefore we currently use user_id = 1.
    #
    # Later this will come from JWT authentication.
    # -----------------------------------------------------

    user_id = 1

    # Find user's bookings
    bookings = db.query(Booking).filter(
        Booking.user_id == user_id
    ).order_by(
        Booking.id.desc()
    ).all()

    result = []

    for booking in bookings:

        # -------------------------------------------------
        # FIND EVENT
        # -------------------------------------------------

        event = db.query(Event).filter(
            Event.id == booking.event_id
        ).first()

        if not event:
            continue

        # -------------------------------------------------
        # FIND SEAT
        # -------------------------------------------------

        seat = db.query(Seat).filter(
            Seat.id == booking.seat_id
        ).first()

        if not seat:
            continue

        # -------------------------------------------------
        # FIND EXISTING TICKET
        # -------------------------------------------------

        ticket = db.query(Ticket).filter(
            Ticket.booking_id == booking.id
        ).first()

        # -------------------------------------------------
        # CREATE TICKET IF IT DOESN'T EXIST
        # -------------------------------------------------

        if not ticket:

            ticket_code = (
                f"EV-{booking.id}-"
                f"{uuid.uuid4().hex[:8].upper()}"
            )

            ticket = Ticket(
                booking_id=booking.id,
                ticket_code=ticket_code,
                status="valid",
                ticket_url="#",
                created_at=datetime.now().isoformat()
            )

            db.add(ticket)
            db.commit()
            db.refresh(ticket)

        # -------------------------------------------------
        # RETURN FRONTEND FORMAT
        # -------------------------------------------------

        result.append({
            "id": str(ticket.id),

            "bookingId": booking.id,

            "eventId": event.id,

            "eventName": event.name,

            "eventDate": event.date,

            "venue": event.venue,

            "seat": seat.seat_number,

            "category": "Standard Reserved",

            "ticketStatus": "READY",

            "ticketUrl": ticket.ticket_url,

            "qrCode": (
                f"EV-VAULT-AUTHENTICATED-"
                f"SECURE-{booking.id}-"
                f"{seat.seat_number}"
            ),

            "ticketCode": ticket.ticket_code,

            "status": ticket.status,

            "createdAt": ticket.created_at
        })

    return result


# =========================================================
# GET SINGLE TICKET
# GET /tickets/{ticket_id}
# =========================================================

@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db)
):
    # Find ticket
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id
    ).first()

    if not ticket:
        raise HTTPException(
            status_code=404,
            detail="Ticket not found"
        )

    # Find booking
    booking = db.query(Booking).filter(
        Booking.id == ticket.booking_id
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

    # Find seat
    seat = db.query(Seat).filter(
        Seat.id == booking.seat_id
    ).first()

    return {
        "id": str(ticket.id),

        "bookingId": booking.id,

        "eventId": event.id,

        "eventName": event.name,

        "eventDate": event.date,

        "venue": event.venue,

        "seat": seat.seat_number if seat else "",

        "category": "Standard Reserved",

        "ticketStatus": "READY",

        "ticketUrl": ticket.ticket_url,

        "qrCode": (
            f"EV-VAULT-AUTHENTICATED-"
            f"SECURE-{booking.id}-"
            f"{seat.seat_number if seat else ''}"
        ),

        "ticketCode": ticket.ticket_code,

        "status": ticket.status,

        "createdAt": ticket.created_at
    }