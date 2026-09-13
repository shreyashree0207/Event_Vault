from database import SessionLocal
from models import Event


events = [
    Event(
        id="evt-cyber-fest-2026",
        name="Neon Horizon Cyber Music Festival",
        category="Music",
        date="2026-10-15",
        time="19:00 PST",
        venue="Apex Arena",
        location="Los Angeles, CA",
        description="The world's premier electronic and synthwave event featuring multi-stage projection mapping, legendary headliners, and ultra-high-density crowd attendance.",
        image="https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1200&q=80",
        starting_price=149.00,
        total_seats=15000,
        available_seats=420,
        is_high_demand="true",
        status="SELLING_FAST"
    ),

    Event(
        id="evt-tech-summit-2026",
        name="Cloud Architecture & AI World Summit",
        category="Technology",
        date="2026-11-04",
        time="09:00 EST",
        venue="Metropolitan Expo Center",
        location="New York, NY",
        description="Connect with system architects, cloud engineers, and security researchers exploring resilient microservices, distributed queues, and high-concurrency systems.",
        image="https://images.unsplash.com/photo-1540575467063-178a50c2df87?auto=format&fit=crop&w=1200&q=80",
        starting_price=299.00,
        total_seats=5000,
        available_seats=1250,
        is_high_demand="true",
        status="AVAILABLE"
    ),

    Event(
        id="evt-champions-league-final",
        name="Global esports Championship Grand Finals",
        category="Sports",
        date="2026-12-10",
        time="18:30 CET",
        venue="Valhalla Dome",
        location="Berlin, Germany",
        description="Witness the ultimate battle in esports history as the top 4 teams worldwide compete live in front of a sold-out arena crowd.",
        image="https://images.unsplash.com/photo-1511512578047-dfb367046420?auto=format&fit=crop&w=1200&q=80",
        starting_price=89.00,
        total_seats=22000,
        available_seats=35,
        is_high_demand="true",
        status="ALMOST_SOLD_OUT"
    ),

    Event(
        id="evt-broadway-quantum",
        name="Quantum Paradox - Immersive Theatre",
        category="Theatre",
        date="2026-10-22",
        time="20:00 EST",
        venue="Starlight Theatre",
        location="Chicago, IL",
        description="A breathtaking mind-bending theatrical drama blending interactive stage craft with temporal soundscapes.",
        image="https://images.unsplash.com/photo-1460723237483-7a6dc9d0b212?auto=format&fit=crop&w=1200&q=80",
        starting_price=110.00,
        total_seats=1800,
        available_seats=310,
        is_high_demand="false",
        status="AVAILABLE"
    ),

    Event(
        id="evt-standup-gala",
        name="International Stand-Up Comedy Night",
        category="Comedy",
        date="2026-11-18",
        time="21:00 PST",
        venue="The Laugh Vault",
        location="San Francisco, CA",
        description="An evening of non-stop comedy featuring 6 award-winning international comedians.",
        image="https://images.unsplash.com/photo-1585699324551-f6c309eedeca?auto=format&fit=crop&w=1200&q=80",
        starting_price=65.00,
        total_seats=1200,
        available_seats=18,
        is_high_demand="true",
        status="SELLING_FAST"
    ),

    Event(
        id="evt-cultural-symphony",
        name="Philharmonic Symphony: Digital Echoes",
        category="Cultural",
        date="2026-12-01",
        time="19:30 GMT",
        venue="Royal Concert Hall",
        location="London, UK",
        description="A magnificent classical symphony orchestra synthesizing traditional orchestral instruments with algorithmic sound generators.",
        image="https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1200&q=80",
        starting_price=120.00,
        total_seats=3000,
        available_seats=890,
        is_high_demand="false",
        status="AVAILABLE"
    )
]


db = SessionLocal()

try:
    # Prevent duplicate insertion
    existing_events = db.query(Event).count()

    if existing_events > 0:
        print(f"Database already contains {existing_events} events.")
        print("No new events were added.")
    else:
        db.add_all(events)
        db.commit()

        print("6 events inserted successfully!")

finally:
    db.close()