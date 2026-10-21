from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Booking, Event, Seat, Ticket
from auth import AuthenticatedUser, get_current_user
from rabbitmq_publisher import publish_ticket_job
from ticket_storage import read_ticket_pdf


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
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    # Find user's bookings
    bookings = db.query(Booking).filter(
        Booking.user_id == current_user.id
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

        if not ticket:
            continue

        is_ready = ticket.status.lower() == "valid" and bool(ticket.object_key)

        result.append({
            "id": str(ticket.id),

            "bookingId": booking.id,

            "eventId": event.id,

            "eventName": event.name,

            "eventDate": event.date,

            "venue": event.venue,

            "seat": seat.seat_number,

            "category": "Standard Reserved",

            "ticketStatus": "READY" if is_ready else ticket.status.upper(),

            "ticketUrl": f"/tickets/{ticket.id}/download" if is_ready else None,

            "qrCode": ticket.ticket_code,

            "ticketCode": ticket.ticket_code,

            "status": ticket.status,

            "createdAt": ticket.created_at
        })

    return result


@router.post("/bookings/{booking_id}/retry")
def retry_ticket_generation(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.user_id == current_user.id,
    ).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Booking not found.")

    ticket = db.query(Ticket).filter(Ticket.booking_id == booking_id).first()
    if ticket is None:
        raise HTTPException(
            status_code=409,
            detail="Ticket record is missing. Contact support to recover this booking.",
        )
    if ticket.status.lower() == "valid" and ticket.object_key:
        return {"status": "READY", "message": "Ticket is already ready."}

    if ticket.status.lower() == "generating":
        started_at = (
            datetime.fromisoformat(ticket.generation_started_at)
            if ticket.generation_started_at else None
        )
        if started_at and started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)
        if started_at and started_at > datetime.now(timezone.utc) - timedelta(minutes=5):
            raise HTTPException(
                status_code=409,
                detail="Ticket generation is already in progress.",
            )

    ticket.status = "pending"
    ticket.error_message = None
    ticket.generation_started_at = None
    db.commit()

    try:
        publish_ticket_job(booking.id)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Ticket retry could not be queued. Please try again. ({exc})",
        )
    return {"status": "PROCESSING", "message": "Ticket retry queued."}


# =========================================================
# GET SINGLE TICKET
# GET /tickets/{ticket_id}
# =========================================================

@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
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
        Booking.id == ticket.booking_id,
        Booking.user_id == current_user.id,
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


@router.get("/{ticket_id}/download")
def download_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    booking = db.query(Booking).filter(
        Booking.id == ticket.booking_id,
        Booking.user_id == current_user.id,
    ).first()
    if booking is None:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    if ticket.status.lower() != "valid" or not ticket.object_key:
        raise HTTPException(
            status_code=409,
            detail="Ticket PDF is not ready for download.",
        )
    try:
        content = read_ticket_pdf(ticket.object_key)
    except FileNotFoundError:
        raise HTTPException(
            status_code=503,
            detail="Ticket PDF is missing. Retry ticket generation.",
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ticket storage is unavailable. Please try again.",
        )

    return Response(
        content=content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{ticket.ticket_code}.pdf"',
            "Cache-Control": "private, no-store",
        },
    )