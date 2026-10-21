import os
import uuid

from locust import HttpUser, between, task
from locust.exception import StopUser


EVENT_ID = os.getenv("LOCUST_EVENT_ID")
EMAIL_DOMAIN = os.getenv("LOCUST_TEST_EMAIL_DOMAIN", "example.invalid")
ALLOW_BOOKINGS = os.getenv("LOCUST_ALLOW_BOOKINGS", "false").lower() == "true"


class EventVaultUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        if not EVENT_ID:
            raise StopUser("Set LOCUST_EVENT_ID to an event in the test database.")

        email = f"locust-{uuid.uuid4().hex}@{EMAIL_DOMAIN}"
        response = self.client.post(
            "/auth/login",
            json={"name": "Event Vault Load Test", "email": email},
            name="/auth/login",
        )
        if response.status_code != 200:
            self.authenticated = False
            return

        payload = response.json()
        self.session_id = payload["user"]["sessionId"]
        self.client.headers["Authorization"] = (
            f"Bearer {payload['accessToken']}"
        )
        self.admission_token = None
        self.booking_done = False
        self.locked_seat = None
        self.authenticated = True

    @task(5)
    def browse_events(self):
        self.client.get("/events")

    @task(3)
    def view_event(self):
        if not getattr(self, "authenticated", False):
            return
        self.client.get(f"/events/{EVENT_ID}")

    @task(2)
    def waiting_room_and_seat_lock(self):
        if not getattr(self, "authenticated", False) or self.booking_done:
            return

        if self.admission_token:
            response = self.client.get(
                f"/waiting-room/{EVENT_ID}/status",
                name="/waiting-room/{event_id}/status",
            )
        else:
            response = self.client.post(
                f"/waiting-room/{EVENT_ID}/join",
                json={},
                name="/waiting-room/{event_id}/join",
            )
        if response.status_code != 200:
            return

        queue = response.json()
        self.admission_token = queue.get("admittedToken")
        if not self.admission_token:
            return

        seats_response = self.client.get(
            f"/events/{EVENT_ID}/seats",
            name="/events/{event_id}/seats",
        )
        if seats_response.status_code != 200:
            return

        seat = next(
            (
                item for item in seats_response.json()
                if item["status"] == "available"
            ),
            None,
        )
        if seat is None:
            return

        seat_code = seat["seatNumber"]
        lock_response = self.client.post(
            "/seat-locks",
            json={
                "event_id": EVENT_ID,
                "seat_code": seat_code,
                "session_id": self.session_id,
                "admission_token": self.admission_token,
            },
            name="/seat-locks [acquire]",
        )
        if lock_response.status_code != 200:
            return
        self.locked_seat = seat_code

        if ALLOW_BOOKINGS:
            booking_response = self.client.post(
                "/bookings",
                json={
                    "eventId": EVENT_ID,
                    "seatCodes": [seat_code],
                    "sessionId": self.session_id,
                    "admissionToken": self.admission_token,
                },
                name="/bookings [test-only]",
            )
            if booking_response.status_code == 200:
                self.booking_done = True
                self.locked_seat = None
                self.admission_token = None
                return

        self.client.delete(
            "/seat-locks",
            json={
                "event_id": EVENT_ID,
                "seat_code": seat_code,
                "session_id": self.session_id,
            },
            name="/seat-locks [release]",
        )
        self.locked_seat = None

    def on_stop(self):
        if (
            getattr(self, "authenticated", False)
            and getattr(self, "locked_seat", None)
        ):
            self.client.delete(
                "/seat-locks",
                json={
                    "event_id": EVENT_ID,
                    "seat_code": self.locked_seat,
                    "session_id": self.session_id,
                },
                name="/seat-locks [cleanup]",
            )
