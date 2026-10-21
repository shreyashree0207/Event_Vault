import unittest
from unittest.mock import patch

from seat_locker import LOCK_DURATION_SECONDS, lock_seat, unlock_seat


class SeatLockerTests(unittest.TestCase):
    def test_acquisition_uses_atomic_set_nx_and_expiration(self):
        with patch("seat_locker.redis_client.set", return_value=True) as set_lock:
            self.assertTrue(lock_seat("event-1", "A1", "session-a"))

        set_lock.assert_called_once_with(
            "seat-lock:event-1:A1",
            "session-a",
            nx=True,
            ex=LOCK_DURATION_SECONDS,
        )

    def test_only_lock_owner_can_release(self):
        with patch("seat_locker.redis_client.eval", return_value=0) as eval_script:
            self.assertFalse(unlock_seat("event-1", "A1", "session-b"))

        args = eval_script.call_args.args
        self.assertIn("redis.call('GET', KEYS[1]) == ARGV[1]", args[0])
        self.assertEqual(args[1:], (1, "seat-lock:event-1:A1", "session-b"))

        with patch("seat_locker.redis_client.eval", return_value=1):
            self.assertTrue(unlock_seat("event-1", "A1", "session-a"))
