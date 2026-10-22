import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel


bearer_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    id: int
    name: str
    email: str
    session_id: str


def _auth_secret() -> bytes:
    secret = os.getenv("AUTH_SECRET_KEY", "")
    if len(secret.encode("utf-8")) < 32:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured. Set AUTH_SECRET_KEY to a secret of at least 32 characters.",
        )
    return secret.encode("utf-8")


def _encode_segment(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode_segment(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: AuthenticatedUser, lifetime_seconds: int = 86400) -> str:
    payload = {
        "sub": user.id,
        "name": user.name,
        "email": user.email,
        "sid": user.session_id,
        "exp": int(time.time()) + lifetime_seconds,
    }
    encoded_payload = _encode_segment(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        _auth_secret(),
        encoded_payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_payload}.{_encode_segment(signature)}"


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Sign in to continue.")

    try:
        encoded_payload, encoded_signature = credentials.credentials.split(".", 1)
        expected_signature = hmac.new(
            _auth_secret(),
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied_signature = _decode_segment(encoded_signature)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("Invalid token signature")

        payload = json.loads(_decode_segment(encoded_payload))
        if (
            not isinstance(payload.get("sub"), int)
            or isinstance(payload.get("sub"), bool)
            or not isinstance(payload.get("name"), str)
            or not isinstance(payload.get("email"), str)
            or not isinstance(payload.get("sid"), str)
            or not payload.get("sid")
            or not isinstance(payload.get("exp"), int)
            or payload["exp"] <= int(time.time())
        ):
            raise ValueError("Invalid or expired token")

        return AuthenticatedUser(
            id=payload["sub"],
            name=payload["name"],
            email=payload["email"],
            session_id=payload["sid"],
        )
    except HTTPException:
        raise
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=401, detail="Invalid or expired sign-in session.")
