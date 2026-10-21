from sqlalchemy import Column, Integer, String, Float, Index, text
from database import Base


# =========================
# USER
# =========================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String, nullable=True)


# =========================
# EVENT
# =========================

class Event(Base):
    __tablename__ = "events"

    # Frontend IDs are strings such as:
    # "evt-cyber-fest-2026"
    id = Column(String, primary_key=True, index=True)

    name = Column(String, nullable=False)
    category = Column(String, nullable=False)

    date = Column(String, nullable=False)
    time = Column(String, nullable=False)

    venue = Column(String, nullable=False)
    location = Column(String, nullable=False)

    description = Column(String, nullable=True)
    image = Column(String, nullable=True)

    starting_price = Column(Float, nullable=False)

    total_seats = Column(Integer, nullable=False)
    available_seats = Column(Integer, nullable=False)

    # Example:
    # true / false
    is_high_demand = Column(String, nullable=False)

    # Examples:
    # AVAILABLE
    # SELLING_FAST
    # ALMOST_SOLD_OUT
    status = Column(String, nullable=False)


# =========================
# SEAT
# =========================

class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)

    event_id = Column(String, nullable=False)

    seat_number = Column(String, nullable=False)

    # Examples:
    # available
    # locked
    # booked
    status = Column(String, nullable=False, default="available")

    __table_args__ = (
        Index("uq_seats_event_number", "event_id", "seat_number", unique=True),
    )


# =========================
# BOOKING
# =========================

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)

    event_id = Column(String, nullable=False)

    seat_id = Column(Integer, nullable=False)

    # Examples:
    # confirmed
    # cancelled
    # pending
    status = Column(String, nullable=False, default="confirmed")

    booking_date = Column(String, nullable=False)

    __table_args__ = (
        Index(
            "uq_bookings_confirmed_seat",
            "seat_id",
            unique=True,
            postgresql_where=text("lower(status) = 'confirmed'"),
        ),
    )


# =========================
# TICKET
# =========================

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(Integer, nullable=False, unique=True, index=True)

    ticket_code = Column(
        String,
        unique=True,
        nullable=False,
        index=True
    )

    # Examples:
    # pending, generating, failed, valid, cancelled, used
    status = Column(String, nullable=False, default="valid")

    ticket_url = Column(String, nullable=True)
    object_key = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    generation_started_at = Column(String, nullable=True)

    created_at = Column(String, nullable=False)