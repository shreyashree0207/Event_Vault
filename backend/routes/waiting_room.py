from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import random
import uuid

from database import SessionLocal
from models import Event


router = APIRouter(
    prefix="/waiting-room",
    tags=["Waiting Room"]
)


# Temporary queue storage
# We will replace this with Redis later.
waiting_rooms = {}


# =========================
# DATABASE SESSION
# =========================

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# =========================
# JOIN WAITING ROOM
# =========================

@router.post("/{event_id}/join")
def join_waiting_room(
    event_id: str,
    db: Session = Depends(get_db)
):

    # Check event exists
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Create queue if it doesn't exist
    if event_id not in waiting_rooms:

        initial_users_ahead = random.randint(180, 430)

        waiting_rooms[event_id] = {
            "eventId": event_id,
            "usersAhead": initial_users_ahead,
            "position": initial_users_ahead + 1,
            "estimatedWaitSeconds": initial_users_ahead * 1,
            "status": "WAITING",
            "joinedAt": datetime.now().isoformat()
        }

    return waiting_rooms[event_id]


# =========================
# GET QUEUE STATUS
# =========================

@router.get("/{event_id}/status")
def get_queue_status(
    event_id: str,
    db: Session = Depends(get_db)
):

    # Check event exists
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Automatically create queue if user
    # asks for status before joining
    if event_id not in waiting_rooms:
        return join_waiting_room(event_id, db)

    queue = waiting_rooms[event_id]

    # Simulate queue advancement
    if queue["status"] == "WAITING":

        decrement = random.randint(15, 40)

        queue["usersAhead"] = max(
            0,
            queue["usersAhead"] - decrement
        )

        queue["position"] = queue["usersAhead"] + 1

        queue["estimatedWaitSeconds"] = (
            queue["usersAhead"]
        )

        # User reaches front
        if queue["usersAhead"] == 0:

            queue["status"] = "ADMITTED"

            queue["admittedToken"] = (
                f"ADMIT-{event_id}-"
                f"{uuid.uuid4().hex[:8].upper()}"
            )

            queue["expiresAt"] = (
                datetime.now() +
                timedelta(minutes=10)
            ).isoformat()

    return queue