from database import SessionLocal
from models import Event, Seat


# Number of demo seats we will create for each event
ROWS = 10
SEATS_PER_ROW = 10


db = SessionLocal()

try:
    events = db.query(Event).all()

    if not events:
        print("No events found in the database.")
        print("Run seed_events.py first.")
    else:
        total_created = 0

        for event in events:

            # Check whether seats already exist for this event
            existing_seats = db.query(Seat).filter(
                Seat.event_id == event.id
            ).count()

            if existing_seats > 0:
                print(
                    f"{event.name}: "
                    f"{existing_seats} seats already exist. Skipping."
                )
                continue

            event_seats = []

            for row_number in range(1, ROWS + 1):

                # A, B, C ... J
                row_letter = chr(64 + row_number)

                for seat_number in range(1, SEATS_PER_ROW + 1):

                    seat = Seat(
                        event_id=event.id,
                        seat_number=f"{row_letter}{seat_number}",
                        status="available"
                    )

                    event_seats.append(seat)

            db.add_all(event_seats)

            total_created += len(event_seats)

            print(
                f"{event.name}: "
                f"{len(event_seats)} seats prepared."
            )

        db.commit()

        print()
        print(f"Total seats created: {total_created}")

finally:
    db.close()