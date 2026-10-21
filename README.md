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
- Booking confirmation and basic seat availability/double-booking protection
- In-memory virtual waiting room prototype
- Ticket generation and status prototype
- My Tickets view
- Browser-local guest profile using a name and mobile number

The current implementation does not include Redis, RabbitMQ, Kubernetes, AWS deployment, autoscaling, or Locust load testing. The frontend contains mock-mode service code and future-oriented comments, but the default path uses the FastAPI backend.

## Technology Stack

- React 19, React Router, and Vite
- JavaScript and CSS
- FastAPI and Uvicorn
- SQLAlchemy ORM
- PostgreSQL with `psycopg2-binary`
- `python-dotenv` for local environment configuration

## Project Structure

```text
Event_Vault/
├── backend/
│   ├── main.py                 # FastAPI app and table creation
│   ├── database.py             # SQLAlchemy engine/session setup
│   ├── models.py               # Database models
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
uvicorn main:app --reload
```

The API runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

## Frontend Setup

In a second terminal, from the project root:

```powershell
npm install
```

The frontend reads the backend URL from `VITE_API_BASE_URL`. Create a root `.env` from `.env.example` if you need to change it:

```text
VITE_API_BASE_URL=http://localhost:8000
```

The login screen stores only a guest name and mobile number in the current
browser. The mobile number is not verified, and this profile is not
authentication or account security. Existing booking and ticket API behavior
continues to use the backend's temporary demo user.

Start the Vite development server:

```powershell
npm run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Running The Project

1. Start PostgreSQL and ensure the `event_vault` database exists.
2. Start FastAPI with `uvicorn main:app --reload` from `backend`.
3. Start Vite with `npm run dev` from the project root.
4. Open `http://localhost:5173` and use the event, waiting room, booking, and ticket flows.

## API Endpoints

### System

- `GET /` - API status message
- `GET /health` - Health check

### Events and Seats

- `GET /events` - List events; supports `search`, `category`, `date`, and `location` query parameters
- `GET /events/{event_id}` - Get one event
- `GET /events/{event_id}/seats` - List seats for an event

### Waiting Room

- `POST /waiting-room/{event_id}/join` - Join an event's in-memory queue
- `GET /waiting-room/{event_id}/status` - Get and advance queue status

### Bookings

- `POST /bookings` - Create a booking from an event ID and seat codes
- `GET /bookings/{booking_id}` - Get one booking
- `GET /bookings/{booking_id}/ticket-status` - Get ticket status for a booking
- `GET /user/bookings` - Get bookings for the authenticated guest identity

### Tickets

- `GET /tickets` - Get tickets for the authenticated guest identity
- `GET /tickets/{ticket_id}` - Get one ticket


## Architecture

```mermaid
flowchart TD
    User[User Browser] --> React[React + Vite frontend]
    React --> FastAPI[FastAPI backend]
    FastAPI --> Events[Events and seats]
    FastAPI --> Waiting[In-memory waiting room prototype]
    FastAPI --> Booking[Booking and seat protection]
    FastAPI --> Tickets[Ticket status and tickets]
    Events --> PostgreSQL[(PostgreSQL)]
    Booking --> PostgreSQL
    Tickets --> PostgreSQL
```

Future architecture may add Redis for queueing and seat locking, RabbitMQ for asynchronous ticket processing, and Docker, Kubernetes, HPA, AWS, and load-testing infrastructure. Those components are not part of the current working system.

## Roadmap

### Done

- [x] React frontend
- [x] FastAPI backend
- [x] PostgreSQL persistence
- [x] Events and seats
- [x] Booking and seat availability protection
- [x] Waiting room prototype
- [x] Ticket prototype
- [x] My Tickets

### Next

- [ ] Redis waiting room
- [ ] Redis seat locking
- [ ] RabbitMQ
- [ ] Real asynchronous Ticket Service
- [ ] Notification Service
- [ ] Docker
- [ ] Kubernetes
- [ ] HPA
- [ ] Locust load testing
- [ ] Failure and recovery testing
- [ ] AWS deployment

## Security Notes

- Never commit `.env`, `backend/.env`, passwords, or database credentials.
- Use `.env.example` and `backend/.env.example` as safe configuration templates.
- Keep PostgreSQL credentials private and use a separate local password for development.
- Generated environments, build output, caches, logs, and local database files are excluded by `.gitignore`.

## License

No license has been added yet. Add one before distributing the project under an open-source license.