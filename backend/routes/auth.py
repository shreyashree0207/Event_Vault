import re
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy import func

from auth import AuthenticatedUser, create_access_token
from database import SessionLocal
from models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class GuestLoginRequest(BaseModel):
    name: str
    email: str

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if len(normalized) < 2 or len(normalized) > 120:
            raise ValueError("Enter your full name (2 to 120 characters).")
        return normalized

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if len(normalized) > 254 or not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("Enter a valid email address.")
        return normalized


@router.post("/login")
def guest_login(
    request: GuestLoginRequest,
    db: Session = Depends(get_db),
):
    try:
        user = db.query(User).filter(
            func.lower(User.email) == request.email
        ).first()

        if user is None:
            user = User(name=request.name, email=request.email)
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            if user.email != request.email:
                user.email = request.email
            if user.name != request.name:
                user.name = request.name
            db.commit()
            db.refresh(user)
    except IntegrityError:
        db.rollback()
        user = db.query(User).filter(
            func.lower(User.email) == request.email
        ).first()
        if user is None:
            raise HTTPException(
                status_code=409,
                detail="Could not create the guest profile. Please try again.",
            )
        user.name = request.name
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Database error while saving the guest profile.",
        )

    identity = AuthenticatedUser(
        id=user.id,
        name=user.name,
        email=user.email,
        session_id=str(uuid.uuid4()),
    )
    return {
        "user": {
            "id": identity.id,
            "name": identity.name,
            "email": identity.email,
            "sessionId": identity.session_id,
        },
        "accessToken": create_access_token(identity),
        "tokenType": "bearer",
    }
