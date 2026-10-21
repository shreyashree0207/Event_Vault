
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi import HTTPException
from redis.exceptions import RedisError

from routes.bookings import BookingRequest, create_booking


class BookingLockTests(unittest.TestCase):

    def setUp(self):
        self.event = SimpleNamespace(
            id="evt-cyber-fest-2026",
            available_seats=10,
            starting_price=25,
            name="Cyber Fest",
            date="2026-11-15",
            venue="Chennai",
        )

        self.seat = SimpleNamespace(
            id=1,
            seat_number="A2",
            status="available",
        )

        event_query = Mock()
        event_query.filter.return_value = event_query
        event_query.with_for_update.return_value = event_query
        event_query.first.return_value = self.event

        seats_query = Mock()
        seats_query.filter.return_value = seats_query
        seats_query.order_by.return_value = seats_query
        seats_query.with_for_update.return_value = seats_query
        seats_query.all.return_value = [self.seat]

        self.db = Mock()
        self.db.query.side_effect = [event_query, seats_query]

        self.request = BookingRequest(
            eventId=self.event.id,
            seatCodes=["A2"],
            sessionId="requesting-session",
        )

    def test_rejects_seat_locked_by_another_session_before_writing(self):
        with patch(
            "routes.bookings.redis_client.get",
            return_value="lock-owning-session",
        ) as redis_get:
            with self.assertRaises(HTTPException) as raised:
                create_booking(self.request, self.db)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail,
            "Seat A2 is temporarily locked by another session.",
        )
        redis_get.assert_called_once_with(
            "seat-lock:evt-cyber-fest-2026:A2"
        )
        self.assertEqual(self.seat.status, "available")
        self.db.add_all.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_allows_booking_when_same_session_owns_lock(self):
        with (
            patch(
                "routes.bookings.redis_client.get",
                return_value="requesting-session",
            ),
            patch("routes.bookings.publish_ticket_job"),
        ):
            result = create_booking(self.request, self.db)

        self.assertEqual(self.seat.status, "booked")
        self.assertEqual(self.event.available_seats, 9)
        self.db.add_all.assert_called_once()
        self.db.commit.assert_called_once()
        self.assertEqual(result["seats"], ["A2"])
        self.assertEqual(result["bookingStatus"], "CONFIRMED")

    def test_rejects_missing_lock_when_session_id_is_provided(self):
        with patch(
            "routes.bookings.redis_client.get",
            return_value=None,
        ):
            with self.assertRaises(HTTPException) as raised:
                create_booking(self.request, self.db)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(
            raised.exception.detail,
            "Seat A2 is not locked by this session.",
        )
        self.assertEqual(self.seat.status, "available")
        self.db.add_all.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_returns_503_and_rolls_back_when_redis_fails(self):
        with patch(
            "routes.bookings.redis_client.get",
            side_effect=RedisError("Redis unavailable"),
        ):
            with self.assertRaises(HTTPException) as raised:
                create_booking(self.request, self.db)

        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(
            raised.exception.detail,
            "Seat-lock service is unavailable. Please try again.",
        )
        self.assertEqual(self.seat.status, "available")
        self.db.add_all.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()

    def test_rejects_duplicate_seat_selection(self):
        duplicate_request = BookingRequest(
            eventId=self.event.id,
            seatCodes=["A2", "A2"],
            sessionId="requesting-session",
        )

        with self.assertRaises(HTTPException) as raised:
            create_booking(duplicate_request, self.db)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.detail,
            "Duplicate seat selections are not allowed",
        )
        self.db.query.assert_not_called()
        self.db.commit.assert_not_called()

    def test_rejects_missing_session_id_before_database_queries(self):
        request_without_session_id = BookingRequest(
            eventId=self.event.id,
            seatCodes=["A2"],
        )

        with self.assertRaises(HTTPException) as raised:
            create_booking(request_without_session_id, self.db)

        self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(
            raised.exception.detail,
            "sessionId is required to confirm a booking",
        )
        self.db.query.assert_not_called()
        self.db.commit.assert_not_called()
        self.db.rollback.assert_called_once()


if __name__ == "__main__":
    unittest.main()
