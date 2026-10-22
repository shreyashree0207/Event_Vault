
import os

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import BaseModel
from redis.exceptions import RedisError

from database import Base, engine, SessionLocal
import models

from routes.auth import router as auth_router
from routes.events import router as events_router
from routes.bookings import router as bookings_router
from routes.waiting_room import router as waiting_room_router
from routes.tickets import router as tickets_router
from auth import AuthenticatedUser, get_current_user

from seat_locker import LOCK_DURATION_SECONDS, lock_seat, unlock_seat
from waiting_room_store import validate_admission_token


class SeatLockRequest(BaseModel):
    event_id: str
    seat_code: str
    session_id: str | None = None
    admission_token: str | None = None


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Event Vault API",
    description="Backend API for the Event Vault ticketing platform",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

default_cors_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "").split(",")
    if origin.strip()
] or default_cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# SEAT LOCK ENDPOINTS
# =========================================================

@app.post("/seat-locks")
def create_seat_lock(
    request: SeatLockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if request.session_id and request.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user.")

    session_id = current_user.session_id
    try:
        admission_valid = bool(
            request.admission_token
            and validate_admission_token(
                request.event_id,
                session_id,
                request.admission_token,
            )
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Waiting-room service is unavailable. Please try again.",
        )
    if not admission_valid:
        raise HTTPException(
            status_code=403,
            detail="A valid waiting-room admission is required to lock seats.",
        )

    db = SessionLocal()
    try:
        event = db.query(models.Event).filter(
            models.Event.id == request.event_id
        ).first()
        if event is None:
            raise HTTPException(status_code=404, detail="Event not found.")

        seat = (
            db.query(models.Seat)
            .filter(
                models.Seat.event_id == request.event_id,
                models.Seat.seat_number == request.seat_code,
            )
            .with_for_update()
            .first()
        )
        if seat is None:
            raise HTTPException(status_code=404, detail="Seat not found.")
        if seat.status.lower() != "available":
            raise HTTPException(
                status_code=409,
                detail="This seat is already booked or unavailable.",
            )

        acquired = lock_seat(request.event_id, request.seat_code, session_id)
        if not acquired:
            raise HTTPException(
                status_code=409,
                detail="This seat is temporarily locked by another session.",
            )

        db.commit()
        return {
            "event_id": request.event_id,
            "seat_code": request.seat_code,
            "session_id": session_id,
            "expires_in_seconds": LOCK_DURATION_SECONDS,
            "message": "Seat temporarily locked.",
        }
    except HTTPException:
        db.rollback()
        raise
    except RedisError:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail="Seat-lock service is unavailable. Please try again.",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while locking the seat.",
        )
    finally:
        db.close()


@app.delete("/seat-locks")
def release_seat_lock(
    request: SeatLockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    if request.session_id and request.session_id != current_user.session_id:
        raise HTTPException(status_code=403, detail="Session does not belong to this user.")

    try:
        released = unlock_seat(
            request.event_id,
            request.seat_code,
            current_user.session_id,
        )
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Seat-lock service is unavailable. Please try again.",
        )

    if not released:
        raise HTTPException(
            status_code=409,
            detail="Lock not found or owned by another session.",
        )

    return {"message": "Seat lock released."}


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

Base.metadata.create_all(bind=engine)


# =========================================================
# REGISTER ROUTES
# =========================================================

app.include_router(events_router)
app.include_router(auth_router)
app.include_router(bookings_router)
app.include_router(waiting_room_router)
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

@app.get("/user/bookings")
def get_user_bookings(
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    db: Session = SessionLocal()

    try:
        bookings = (
            db.query(models.Booking)
            .filter(models.Booking.user_id == current_user.id)
            .order_by(models.Booking.id.desc())
            .all()
        )

        result = []

        for booking in bookings:
            event = (
                db.query(models.Event)
                .filter(models.Event.id == booking.event_id)
                .first()
            )

            if not event:
                continue

            seat = (
                db.query(models.Seat)
                .filter(models.Seat.id == booking.seat_id)
                .first()
            )

            ticket_price = event.starting_price
            service_fee = round(ticket_price * 0.12, 2)

            result.append({
                "id": booking.id,
                "userId": booking.user_id,
                "eventId": booking.event_id,
                "eventName": event.name,
                "eventDate": event.date,
                "venue": event.venue,
                "seats": [seat.seat_number] if seat else [],
                "ticketPrice": ticket_price,
                "serviceFee": service_fee,
                "totalAmount": round(ticket_price + service_fee, 2),
                "paymentStatus": "PAID",
                "bookingStatus": booking.status.upper(),
                "createdAt": booking.booking_date,
                "ticketStatus": "READY",
            })

        return result
    finally:
        db.close()
