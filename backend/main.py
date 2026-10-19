from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, SessionLocal
import models

from routes.events import router as events_router
from routes.bookings import router as bookings_router
from routes.waiting_room import router as waiting_room_router
from routes.tickets import router as tickets_router
from pydantic import BaseModel
from seat_locker import lock_seat, unlock_seat, new_session_id


class SeatLockRequest(BaseModel):
    event_id: str
    seat_code: str
    session_id: str | None = None


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Event Vault API",
    description="Backend API for the Event Vault ticketing platform",
    version="1.0.0"
)


@app.post("/seat-locks")
def create_seat_lock(request: SeatLockRequest):
    session_id = request.session_id or new_session_id()

    acquired = lock_seat(
        request.event_id,
        request.seat_code,
        session_id,
    )

    if not acquired:
        raise HTTPException(
            status_code=409,
            detail="This seat is temporarily locked by another session.",
        )

    return {
        "event_id": request.event_id,
        "seat_code": request.seat_code,
        "session_id": session_id,
        "expires_in_seconds": 300,
        "message": "Seat temporarily locked.",
    }


@app.delete("/seat-locks")
def release_seat_lock(request: SeatLockRequest):
    if not request.session_id:
        raise HTTPException(
            status_code=400,
            detail="session_id is required to release a seat lock.",
        )

    released = unlock_seat(
        request.event_id,
        request.seat_code,
        request.session_id,
    )

    if not released:
        raise HTTPException(
            status_code=409,
            detail="Lock not found or owned by another session.",
        )

    return {"message": "Seat lock released."}


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(
    bind=engine
)


# =========================================================
# REGISTER ROUTES
# =========================================================

app.include_router(
    events_router
)

app.include_router(
    bookings_router
)

app.include_router(
    waiting_room_router
)

app.include_router(tickets_router)

# =========================================================
# ROOT
# GET /
# =========================================================

@app.get("/")
def root():
    return {
        "message": "Event Vault API is running"
    }


# =========================================================
# HEALTH CHECK
# GET /health
# =========================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# =========================================================
# GET USER BOOKINGS
# GET /user/bookings
# =========================================================
#
# TEMPORARY USER SYSTEM
#
# Authentication/JWT is not implemented yet.
# Therefore we currently use user_id = 1.
#
# Later:
#
# Login
#   ↓
# JWT
#   ↓
# actual user ID
#   ↓
# user's bookings
#
# =========================================================

@app.get("/user/bookings")
def get_user_bookings():

    db: Session = SessionLocal()

    try:

        # Temporary logged-in user
        user_id = 1

        # Find all bookings for this user
        bookings = db.query(models.Booking).filter(
            models.Booking.user_id == user_id
        ).order_by(
            models.Booking.id.desc()
        ).all()

        result = []

        for booking in bookings:

            # -------------------------------------------------
            # FIND EVENT
            # -------------------------------------------------

            event = db.query(models.Event).filter(
                models.Event.id == booking.event_id
            ).first()

            if not event:
                continue

            # -------------------------------------------------
            # FIND SEAT
            # -------------------------------------------------

            seat = db.query(models.Seat).filter(
                models.Seat.id == booking.seat_id
            ).first()

            seats = []

            if seat:
                seats.append(
                    seat.seat_number
                )

            # -------------------------------------------------
            # PAYMENT CALCULATION
            # -------------------------------------------------

            ticket_price = event.starting_price

            service_fee = round(
                ticket_price * 0.12,
                2
            )

            total_amount = round(
                ticket_price + service_fee,
                2
            )

            # -------------------------------------------------
            # ADD BOOKING TO RESPONSE
            # -------------------------------------------------

            result.append({

                "id": booking.id,

                "userId": booking.user_id,

                "eventId": booking.event_id,

                "eventName": event.name,

                "eventDate": event.date,

                "venue": event.venue,

                "seats": seats,

                "ticketPrice": ticket_price,

                "serviceFee": service_fee,

                "totalAmount": total_amount,

                "paymentStatus": "PAID",

                "bookingStatus": booking.status.upper(),

                "createdAt": booking.booking_date,

                # Temporary ticket status
                "ticketStatus": "READY"
            })

        return result

    finally:

        db.close()