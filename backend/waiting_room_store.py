import os
import time
import uuid
from datetime import datetime, timezone

from redis.exceptions import RedisError

from redis_client import redis_client


ADMISSION_LIMIT = int(os.getenv("WAITING_ROOM_ADMISSION_LIMIT", "25"))
ADMISSION_TTL_SECONDS = int(
    os.getenv("WAITING_ROOM_ADMISSION_TTL_SECONDS", "600")
)
MAX_QUEUE_SIZE = int(os.getenv("WAITING_ROOM_MAX_QUEUE_SIZE", "5000"))
QUEUE_TTL_SECONDS = int(os.getenv("WAITING_ROOM_QUEUE_TTL_SECONDS", "86400"))
STATE_TTL_SECONDS = int(os.getenv("WAITING_ROOM_STATE_TTL_SECONDS", "86400"))

if min(
    ADMISSION_LIMIT,
    ADMISSION_TTL_SECONDS,
    MAX_QUEUE_SIZE,
    QUEUE_TTL_SECONDS,
    STATE_TTL_SECONDS,
) <= 0:
    raise RuntimeError("Waiting-room capacity and TTL settings must be positive.")


QUEUE_STATUS_SCRIPT = """
local queue = KEYS[1]
local admitted = KEYS[2]
local token_key = KEYS[3]
local state_key = KEYS[4]
local session_id = ARGV[1]
local now = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local admission_ttl = tonumber(ARGV[4])
local new_token = ARGV[5]
local max_queue = tonumber(ARGV[6])
local state_ttl = tonumber(ARGV[7])
local queue_ttl = tonumber(ARGV[8])

redis.call('ZREMRANGEBYSCORE', admitted, '-inf', now)
redis.call('ZREMRANGEBYSCORE', queue, '-inf', now - queue_ttl)

local state = redis.call('GET', state_key)
if state == 'COMPLETED' or state == 'EXPIRED' then
    return {state, 0, '', 0, redis.call('ZCARD', queue)}
end

if state == 'ADMITTED' then
    local token = redis.call('GET', token_key)
    local expiry = redis.call('ZSCORE', admitted, session_id)
    if token and expiry then
        return {'ADMITTED', 0, token, expiry, redis.call('ZCARD', queue)}
    end
    redis.call('SET', state_key, 'EXPIRED', 'EX', state_ttl)
    redis.call('ZREM', admitted, session_id)
    return {'EXPIRED', 0, '', 0, redis.call('ZCARD', queue)}
end

if not redis.call('ZSCORE', queue, session_id) then
    if redis.call('ZCARD', queue) >= max_queue then
        return {'FULL', 0, '', 0, redis.call('ZCARD', queue)}
    end
    redis.call('ZADD', queue, 'NX', now, session_id)
    redis.call('EXPIRE', queue, queue_ttl / 1000)
    redis.call('SET', state_key, 'WAITING', 'EX', state_ttl)
end

local rank = redis.call('ZRANK', queue, session_id)
if not rank then
    return {'EXPIRED', 0, '', 0, redis.call('ZCARD', queue)}
end

local free_slots = capacity - redis.call('ZCARD', admitted)
if rank < free_slots then
    local expiry = now + admission_ttl
    redis.call('ZREM', queue, session_id)
    redis.call('ZADD', admitted, expiry, session_id)
    redis.call('EXPIRE', admitted, state_ttl)
    redis.call('SET', token_key, new_token, 'PX', admission_ttl)
    redis.call('SET', state_key, 'ADMITTED', 'EX', state_ttl)
    return {'ADMITTED', 0, new_token, expiry, redis.call('ZCARD', queue)}
end

return {'WAITING', rank, '', 0, redis.call('ZCARD', queue)}
"""

VALIDATE_ADMISSION_SCRIPT = """
local token = redis.call('GET', KEYS[1])
local expiry = redis.call('ZSCORE', KEYS[2], ARGV[1])
if token == ARGV[2] and expiry and tonumber(expiry) > tonumber(ARGV[3]) then
    return 1
end
return 0
"""

RELEASE_ADMISSION_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    redis.call('DEL', KEYS[1])
    redis.call('ZREM', KEYS[2], ARGV[2])
    redis.call('SET', KEYS[3], 'COMPLETED', 'EX', ARGV[3])
    return 1
end
return 0
"""


def _keys(event_id: str, session_id: str) -> tuple[str, str, str, str]:
    prefix = f"waiting-room:{event_id}"
    return (
        f"{prefix}:queue",
        f"{prefix}:admitted",
        f"{prefix}:token:{session_id}",
        f"{prefix}:state:{session_id}",
    )


def get_queue_status(event_id: str, session_id: str) -> dict:
    queue_key, admitted_key, token_key, state_key = _keys(event_id, session_id)
    now = int(time.time() * 1000)
    result = redis_client.eval(
        QUEUE_STATUS_SCRIPT,
        4,
        queue_key,
        admitted_key,
        token_key,
        state_key,
        session_id,
        now,
        ADMISSION_LIMIT,
        ADMISSION_TTL_SECONDS * 1000,
        uuid.uuid4().hex + uuid.uuid4().hex,
        MAX_QUEUE_SIZE,
        STATE_TTL_SECONDS,
        QUEUE_TTL_SECONDS * 1000,
    )

    status, users_ahead, token, expires_at, queue_length = result
    response = {
        "eventId": event_id,
        "status": status,
        "usersAhead": int(users_ahead),
        "position": int(users_ahead) + 1,
        "estimatedWaitSeconds": int(users_ahead) * 5,
        "queueLength": int(queue_length),
    }
    if status == "ADMITTED":
        expiry_ms = int(float(expires_at))
        response.update({
            "admittedToken": token,
            "expiresAt": datetime.fromtimestamp(
                expiry_ms / 1000,
                tz=timezone.utc,
            ).isoformat(),
            "expiresInSeconds": ADMISSION_TTL_SECONDS,
        })
    return response


def validate_admission_token(
    event_id: str,
    session_id: str,
    admission_token: str,
) -> bool:
    _, admitted_key, token_key, _ = _keys(event_id, session_id)
    return bool(
        redis_client.eval(
            VALIDATE_ADMISSION_SCRIPT,
            2,
            token_key,
            admitted_key,
            session_id,
            admission_token,
            int(time.time() * 1000),
        )
    )


def release_admission(
    event_id: str,
    session_id: str,
    admission_token: str,
) -> bool:
    _, admitted_key, token_key, state_key = _keys(event_id, session_id)
    return bool(
        redis_client.eval(
            RELEASE_ADMISSION_SCRIPT,
            3,
            token_key,
            admitted_key,
            state_key,
            admission_token,
            session_id,
            STATE_TTL_SECONDS,
        )
    )


def leave_queue_or_admission(
    event_id: str,
    session_id: str,
    admission_token: str | None = None,
) -> bool:
    queue_key, admitted_key, token_key, state_key = _keys(event_id, session_id)
    if admission_token:
        release_admission(event_id, session_id, admission_token)
    redis_client.zrem(queue_key, session_id)
    redis_client.zrem(admitted_key, session_id)
    redis_client.delete(token_key)
    redis_client.delete(state_key)
    return True

