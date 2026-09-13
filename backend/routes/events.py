from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Event, Seat


router = APIRouter(
    prefix="/events",
    tags=["Events"]
)


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
# GET ALL EVENTS
# =========================

@router.get("")
def get_events(
    search: str = "",
    category: str = "",
    date: str = "",
    location: str = "",
    db: Session = Depends(get_db)
):
    query = db.query(Event)

    # Search by event name, description or venue
    if search:
        search_text = f"%{search}%"

        query = query.filter(
            (Event.name.ilike(search_text)) |
            (Event.description.ilike(search_text)) |
            (Event.venue.ilike(search_text))
        )

    # Filter by category
    if category and category.lower() != "all":
        query = query.filter(
            Event.category.ilike(category)
        )

    # Filter by date
    if date:
        query = query.filter(
            Event.date >= date
        )

    # Filter by location
    if location:
        query = query.filter(
            Event.location.ilike(f"%{location}%")
        )

    events = query.all()

    return [
        {
            "id": event.id,
            "name": event.name,
            "category": event.category,
            "date": event.date,
            "time": event.time,
            "venue": event.venue,
            "location": event.location,
            "description": event.description,
            "image": event.image,
            "startingPrice": event.starting_price,
            "totalSeats": event.total_seats,
            "availableSeats": event.available_seats,
            "isHighDemand": event.is_high_demand == "true",
            "status": event.status
        }
        for event in events
    ]


# =========================
# GET EVENT BY ID
# =========================

@router.get("/{event_id}")
def get_event(
    event_id: str,
    db: Session = Depends(get_db)
):
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    return {
        "id": event.id,
        "name": event.name,
        "category": event.category,
        "date": event.date,
        "time": event.time,
        "venue": event.venue,
        "location": event.location,
        "description": event.description,
        "image": event.image,
        "startingPrice": event.starting_price,
        "totalSeats": event.total_seats,
        "availableSeats": event.available_seats,
        "isHighDemand": event.is_high_demand == "true",
        "status": event.status
    }
# =========================
# GET SEATS FOR AN EVENT
# =========================

@router.get("/{event_id}/seats")
def get_event_seats(
    event_id: str,
    db: Session = Depends(get_db)
):
    # Check that the event exists
    event = db.query(Event).filter(
        Event.id == event_id
    ).first()

    if not event:
        raise HTTPException(
            status_code=404,
            detail="Event not found"
        )

    # Get all seats belonging to this event
    seats = db.query(Seat).filter(
        Seat.event_id == event_id
    ).order_by(Seat.id).all()

    return [
        {
            "id": seat.id,
            "eventId": seat.event_id,
            "seatNumber": seat.seat_number,
            "status": seat.status
        }
        for seat in seats
    ]