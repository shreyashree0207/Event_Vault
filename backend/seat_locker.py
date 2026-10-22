import uuid
import os

from redis_client import redis_client

LOCK_DURATION_SECONDS = int(os.getenv("SEAT_LOCK_TTL_SECONDS", "300"))
if LOCK_DURATION_SECONDS <= 0:
    raise RuntimeError("SEAT_LOCK_TTL_SECONDS must be a positive integer.")


def lock_seat(event_id: str, seat_code: str, session_id: str) -> bool:
    """
    Temporarily lock a seat for one session.
    Returns True if the lock is acquired, otherwise False.
    """
    key = f"seat-lock:{event_id}:{seat_code}"

    return bool(
        redis_client.set(
            key,
            session_id,
            nx=True,
            ex=LOCK_DURATION_SECONDS,
        )
    )


def unlock_seat(event_id: str, seat_code: str, session_id: str) -> bool:
    """
    Release a seat only when the requesting session owns its lock.
    """
    key = f"seat-lock:{event_id}:{seat_code}"

    script = """
    if redis.call('GET', KEYS[1]) == ARGV[1] then
        return redis.call('DEL', KEYS[1])
    else
        return 0
    end
    """

    return bool(
        redis_client.eval(
            script,
            1,
            key,
            session_id,
        )
    )


def new_session_id() -> str:
    return str(uuid.uuid4())