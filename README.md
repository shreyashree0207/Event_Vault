# Event Vault

> Control the Crowd. Protect the Booking. Recover from Failure.

Event Vault is a cloud-native event ticket booking platform prototype built around high-traffic admission, seat protection, reliable booking, and recovery-oriented architecture.

## What Is Event Vault?

Event Vault explores how an event ticketing system can remain usable during high-demand ticket releases. The current repository is a working React, FastAPI, and PostgreSQL application with a simulated waiting room and ticket workflow. More advanced distributed components are documented as future architecture rather than presented as implemented features.

## Current Features

- React frontend with Vite
- FastAPI backend
- PostgreSQL persistence through SQLAlchemy
- Event listing and event details
- Real event and seat data loaded from PostgreSQL
- Interactive seat selection
- PostgreSQL-backed booking with database seat constraints
- Redis seat locks and a bounded, server-enforced virtual waiting room
- Ticket generation and status prototype
- My Tickets view
- PostgreSQL-backed guest identity using a name and email address
- Configurable Locust journeys (load testing is not run automatically)

The current implementation does not include S3 ticket storage, Kubernetes,
AWS deployment, or autoscaling. RabbitMQ ticket generation is a prototype.
The default frontend path uses the FastAPI backend.

## Technology Stack

- React 19, React Router, and Vite
- JavaScript and CSS
- FastAPI and Uvicorn
- SQLAlchemy ORM
- PostgreSQL with `psycopg2-binary`
- Redis for seat locking and the waiting room
- Locust for configurable test journeys
- `python-dotenv` for local environment configuration

## Project Structure

```text
Event_Vault/
├── backend/
│   ├── main.py                 # FastAPI app and table creation
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── models.py               # Database models
│   ├── auth.py                 # Signed guest session tokens
│   ├── waiting_room_store.py   # Atomic Redis admission state
│   ├── migrations/             # Non-destructive PostgreSQL migrations
│   ├── tests/
│   ├── locustfile.py
│   ├── requirements.txt
│   ├── seed_events.py           # Demo event data
│   ├── seed_seats.py            # Demo seats for existing events
│   └── routes/
│       ├── auth.py
│       ├── events.py
│       ├── bookings.py
│       ├── waiting_room.py
│       └── tickets.py
├── public/
├── src/
│   ├── components/
│   ├── data/                   # Frontend fallback/demo data
│   ├── pages/
│   ├── services/               # API client and domain services
│   ├── App.jsx
│   └── main.jsx
├── .env.example
├── package.json
├── package-lock.json
└── vite.config.js
```

## Prerequisites

- Node.js and npm
- Python 3.11 or newer
- PostgreSQL
- Redis
- RabbitMQ only when running the ticket worker

## Database Setup

1. Start PostgreSQL.
2. Create a database named `event_vault`:

   ```sql
   CREATE DATABASE event_vault;
   ```

3. Create `backend/.env` from `backend/.env.example` and set your local PostgreSQL password:

   ```text
   DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/event_vault
   ```

   Configure `CORS_ORIGINS` with the frontend origin(s). For a LAN frontend, include `http://<FRONTEND_HOST_LAN_IP>:5173`. Do not commit `backend/.env`.

   Before upgrading an existing database, take a backup and apply these
   migrations in order from the repository root. Each migration refuses to
   proceed if it detects duplicate data that would violate the new constraints:

   ```powershell
   psql -d event_vault -v ON_ERROR_STOP=1 -f backend/migrations/001_guest_login.sql
   psql -d event_vault -v ON_ERROR_STOP=1 -f backend/migrations/002_seat_lock_constraints.sql
   ```

   Set `AUTH_SECRET_KEY`, `REDIS_HOST`, `REDIS_PORT`, `SEAT_LOCK_TTL_SECONDS`,
   and the `WAITING_ROOM_*` settings in `backend/.env`. Keep PostgreSQL and
   Redis reachable only by the backend and trusted operators.

4. Create the backend environment and install dependencies:

   ```powershell
   cd backend
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

When the backend starts, `main.py` creates the SQLAlchemy tables if they do not already exist. With the virtual environment active, seed demo data from the `backend` directory:

```powershell
python seed_events.py
python seed_seats.py
```

Run `seed_events.py` before `seed_seats.py`. Both scripts skip data that already exists.

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`. Binding to `0.0.0.0` is for trusted local-network development only; production should run behind HTTPS and a restricted network boundary.

## Frontend Setup

In a second terminal, from the project root:

```powershell
npm install
```

The frontend reads the backend URL from `VITE_API_BASE_URL`. Create a root `.env` from `.env.example` if you need to change it:

```text
VITE_API_BASE_URL=http://localhost:8000
```

The name-and-email login is guest/demo identification only. Email addresses
are not verified, so this is not secure authentication and users can claim
another person's email. The backend issues a signed, short-lived session token
and uses its server-verified user identity for booking and ticket operations;
never treat the entered email as proof of account ownership.

For local or LAN development, set `VITE_API_BASE_URL` to the API host that is
reachable from the browser. On a second laptop, `localhost` means that second
laptop, not the development machine; use the development machine's reachable
LAN address in an untracked `.env.local` file. Configure `CORS_ORIGINS` in
`backend/.env` for the frontend origin. For production builds, copy
`.env.production.example` to the appropriate Vite production environment
configuration and use the deployed HTTPS API URL. Every `VITE_*` value is
public in the browser bundle and must never contain secrets.

Set `AUTH_SECRET_KEY` in `backend/.env` to a private random value of at least
32 characters (for example, generate one with
`python -c "import secrets; print(secrets.token_urlsafe(48))"`). Do not reuse
the example placeholder or commit the configured key.

For an existing PostgreSQL database, back it up and apply
`backend/migrations/001_guest_login.sql` once before starting the updated
backend. It normalizes stored email addresses, stops if duplicates would
collide, allows the legacy password column to be null, and creates a
case-insensitive unique index. It does not drop tables or booking data. New
databases use the updated model schema automatically.

Start the Vite development server:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Running The Project

1. Start PostgreSQL and ensure the `event_vault` database exists.
2. Start FastAPI with `uvicorn main:app --reload` from `backend`.
3. Start Vite with `npm run dev` from the project root.
4. Open `http://localhost:5173`, sign in with a name and email address, and use the event, waiting room, booking, and ticket flows.

## Waiting-room and seat-lock behavior

Redis atomically admits no more than `WAITING_ROOM_ADMISSION_LIMIT` active
sessions per event. The Redis-backed queue has a separate maximum length, and
admission tokens expire after `WAITING_ROOM_ADMISSION_TTL_SECONDS`. Booking and
seat-lock endpoints verify the token server-side; navigating directly to the
booking URL or calling the ordinary API without an admitted token is rejected.
Seat locks use `SEAT_LOCK_TTL_SECONDS` and only the signed session that owns a
lock can release it. PostgreSQL remains authoritative for confirmed bookings.

## Locust load testing

Load testing is intentionally not run by the application or CI by default.
Use a dedicated test/staging database and Redis instance, never the live
booking environment. The test creates unique guest rows and will only create
bookings when explicitly enabled:

```powershell
cd backend
$env:LOCUST_EVENT_ID = "evt-test-event"
$env:LOCUST_TEST_EMAIL_DOMAIN = "example.invalid"
locust -f locustfile.py --host http://localhost:8000 --headless -u 10 -r 2 -t 2m --csv=event-vault-load
```

The default journey visits events, joins the waiting room, acquires and
releases a seat lock, and does not create bookings. For disposable test data
only, set `$env:LOCUST_ALLOW_BOOKINGS = "true"` to exercise one confirmed
booking per admitted simulated user. Adjust `-u` (users), `-r` (users spawned
per second), and `-t` (duration) gradually. Locust's CSV/console report
provides request rates, response-time percentiles, and failures. Correlate it
with backend/Redis metrics and inspect test bookings for duplicates. No
load-test results are claimed for this repository until run against an
approved staging environment.

## API Endpoints

### System

- `GET /` - API status message
- `GET /health` - Health check

### Guest identity

- `POST /auth/login` - Create or retrieve a guest profile and issue a signed session token. This is not verified authentication.

### Events and Seats

- `GET /events` - List events; supports `search`, `category`, `date`, and `location` query parameters
- `GET /events/{event_id}` - Get one event
- `GET /events/{event_id}/seats` - List seats and current Redis lock state (requires guest session)

### Waiting Room

- `POST /waiting-room/{event_id}/join` - Join or restore the authenticated session's Redis queue entry
- `GET /waiting-room/{event_id}/status` - Get queue position or admission state

### Bookings

- `POST /bookings` - Create a booking from an event ID and seat codes
- `GET /bookings/{booking_id}` - Get one booking
- `GET /bookings/{booking_id}/ticket-status` - Get ticket status for a booking
- `GET /user/bookings` - Get bookings for the authenticated guest identity

Booking, booking-detail, ticket-status, seat-lock, and ticket routes require
the bearer token returned by `POST /auth/login`. The frontend sends it
automatically. Logging out removes the token from that browser; guest identity
does not provide account recovery or protection against email impersonation.

### Tickets

- `GET /tickets` - Get tickets for the authenticated guest identity
- `GET /tickets/{ticket_id}` - Get one ticket


## Architecture

```mermaid
flowchart TD
    User[User Browser] --> React[React + Vite frontend]
    React --> FastAPI[FastAPI backend]
    FastAPI --> Events[Events and seats]
    FastAPI --> Waiting[Redis waiting room and admission tokens]
    FastAPI --> Booking[Booking and seat protection]
    FastAPI --> Tickets[Ticket status and tickets]
    Events --> PostgreSQL[(PostgreSQL)]
    Booking --> PostgreSQL
    Tickets --> PostgreSQL
    Waiting --> Redis[(Redis)]
    Booking --> Redis
```

Future architecture may add S3 ticket storage and production cloud hosting.

## Roadmap

### Done

- [x] React frontend
- [x] FastAPI backend
- [x] PostgreSQL persistence
- [x] Events and seats
- [x] Booking and seat availability protection
- [x] Redis seat locking
- [x] Redis-backed waiting room and admission enforcement
- [x] Ticket prototype
- [x] My Tickets

### Next

- [x] Redis waiting room
- [x] Redis seat locking
- [ ] RabbitMQ
- [ ] Real asynchronous Ticket Service
- [ ] Notification Service
- [ ] Docker
- [ ] Kubernetes
- [ ] HPA
- [x] Locust journey configuration (load test execution pending staging)
- [ ] Failure and recovery testing
- [ ] AWS deployment

## Security Notes

- Never commit `.env`, `backend/.env`, passwords, or database credentials.
- Use `.env.example` and `backend/.env.example` as safe configuration templates.
- Keep PostgreSQL credentials private and use a separate local password for development.
- Generated environments, build output, caches, logs, and local database files are excluded by `.gitignore`.

## License

No license has been added yet. Add one before distributing the project under an open-source license.