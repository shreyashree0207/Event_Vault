from fastapi import APIRouter, Depends, HTTPException
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from auth import AuthenticatedUser, get_current_user
from database import SessionLocal
from models import Event
from waiting_room_store import get_queue_status


router = APIRouter(prefix="/waiting-room", tags=["Waiting Room"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_status(
    event_id: str,
    db: Session,
    current_user: AuthenticatedUser,
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found.")

    try:
        return get_queue_status(event_id, current_user.session_id)
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="Waiting-room service is unavailable. Please try again.",
        )


@router.post("/{event_id}/join")
def join_waiting_room(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return _get_status(event_id, db, current_user)


@router.get("/{event_id}/status")
def get_queue_status_endpoint(
    event_id: str,
    db: Session = Depends(get_db),
    current_user: AuthenticatedUser = Depends(get_current_user),
):
    return _get_status(event_id, db, current_user)
