import unittest
from unittest.mock import patch

from waiting_room_store import get_queue_status, release_admission, validate_admission_token


class WaitingRoomStoreTests(unittest.TestCase):
    def test_admitted_response_contains_server_generated_token_and_expiry(self):
        with patch(
            "waiting_room_store.redis_client.eval",
            return_value=["ADMITTED", 0, "opaque-token", "1900000000000", 4],
        ) as eval_script:
            status = get_queue_status("event-1", "session-a")

        self.assertEqual(status["status"], "ADMITTED")
        self.assertEqual(status["admittedToken"], "opaque-token")
        self.assertEqual(status["queueLength"], 4)
        self.assertEqual(eval_script.call_args.args[1], 4)

    def test_waiting_response_reports_queue_position(self):
        with patch(
            "waiting_room_store.redis_client.eval",
            return_value=["WAITING", 3, "", 0, 8],
        ):
            status = get_queue_status("event-1", "session-a")

        self.assertEqual(status["usersAhead"], 3)
        self.assertEqual(status["position"], 4)

    def test_admission_validation_and_release_use_atomic_scripts(self):
        with patch(
            "waiting_room_store.redis_client.eval",
            side_effect=[1, 1],
        ) as eval_script:
            self.assertTrue(
                validate_admission_token("event-1", "session-a", "opaque-token")
            )
            self.assertTrue(
                release_admission("event-1", "session-a", "opaque-token")
            )

        self.assertEqual(eval_script.call_count, 2)
        self.assertIn("token == ARGV[2]", eval_script.call_args_list[0].args[0])
        self.assertIn(
            "redis.call('GET', KEYS[1]) == ARGV[1]",
            eval_script.call_args_list[1].args[0],
        )

