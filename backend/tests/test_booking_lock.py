import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException

from routes.bookings import BookingRequest, create_booking


class BookingLockTests(unittest.TestCase):
    def test_rejects_seat_locked_by_another_session_before_writing(self):
        event = SimpleNamespace(
            id="evt-cyber-fest-2026",
            available_seats=10,
            starting_price=25,
        )
        seat = SimpleNamespace(
            id=1,
            seat_number="A2",
            status="available",
        )

        event_query = Mock()
        event_query.filter.return_value = event_query
        event_query.first.return_value = event

        seats_query = Mock()
        seats_query.filter.return_value = seats_query
        seats_query.all.return_value = [seat]

        db = Mock()
        db.query.side_effect = [event_query, seats_query]
        request = BookingRequest(
            eventId=event.id,
            seatCodes=["A2"],
            sessionId="requesting-session",
        )

        with patch(
            "routes.bookings.redis_client.get",
            return_value="lock-owning-session",
        ) as redis_get:
            with self.assertRaises(HTTPException) as raised:
                create_booking(request, db)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail,
            "Seat A2 is temporarily locked by another session.",
        )
        redis_get.assert_called_once_with(
            "seat-lock:evt-cyber-fest-2026:A2"
        )
        self.assertEqual(seat.status, "available")
        db.add.assert_not_called()
        db.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
