import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError

from auth import AuthenticatedUser, create_access_token, get_current_user
from routes.auth import GuestLoginRequest, guest_login


class GuestLoginValidationTests(unittest.TestCase):
    def test_normalizes_name_and_email(self):
        request = GuestLoginRequest(
            name="  Alex   Mercer ",
            email="  ALEX@Example.COM ",
        )

        self.assertEqual(request.name, "Alex Mercer")
        self.assertEqual(request.email, "alex@example.com")

    def test_rejects_short_name_and_invalid_email(self):
        with self.assertRaises(ValidationError):
            GuestLoginRequest(name="A", email="alex@example.com")
        with self.assertRaises(ValidationError):
            GuestLoginRequest(name="Alex Mercer", email="invalid")


class GuestTokenTests(unittest.TestCase):
    def setUp(self):
        self.user = AuthenticatedUser(
            id=12,
            name="Alex Mercer",
            email="alex@example.com",
            session_id="session-unique",
        )

    def test_signed_token_restores_user_and_session(self):
        with patch.dict(os.environ, {"AUTH_SECRET_KEY": "x" * 40}):
            token = create_access_token(self.user)
            restored = get_current_user(
                SimpleNamespace(scheme="Bearer", credentials=token)
            )

        self.assertEqual(restored, self.user)

    def test_rejects_invalid_signature(self):
        with patch.dict(os.environ, {"AUTH_SECRET_KEY": "x" * 40}):
            token = create_access_token(self.user)
        with patch.dict(os.environ, {"AUTH_SECRET_KEY": "y" * 40}):
            with self.assertRaises(HTTPException) as raised:
                get_current_user(
                    SimpleNamespace(scheme="Bearer", credentials=token)
                )
        self.assertEqual(raised.exception.status_code, 401)

    def test_rejects_expired_token(self):
        with patch.dict(os.environ, {"AUTH_SECRET_KEY": "x" * 40}):
            token = create_access_token(self.user, lifetime_seconds=-1)
            with self.assertRaises(HTTPException) as raised:
                get_current_user(
                    SimpleNamespace(scheme="Bearer", credentials=token)
                )
        self.assertEqual(raised.exception.status_code, 401)


class GuestLoginPersistenceTests(unittest.TestCase):
    def test_creates_persistent_guest_and_returns_signed_session(self):
        db = unittest.mock.Mock()
        query = db.query.return_value
        query.filter.return_value.first.return_value = None
        db.refresh.side_effect = lambda user: setattr(user, "id", 42)

        with patch("routes.auth.create_access_token", return_value="signed-token"):
            response = guest_login(
                GuestLoginRequest(
                    name="Alex Mercer",
                    email="ALEX@example.com",
                ),
                db,
            )

        created_user = db.add.call_args.args[0]
        self.assertEqual(created_user.name, "Alex Mercer")
        self.assertEqual(created_user.email, "alex@example.com")
        self.assertIsNone(created_user.password)
        self.assertEqual(response["user"]["id"], 42)
        self.assertEqual(response["accessToken"], "signed-token")
        db.commit.assert_called_once()

    def test_retrieves_existing_user_for_normalized_email(self):
        user = SimpleNamespace(
            id=17,
            name="Original Name",
            email="alex@example.com",
            password=None,
        )
        db = unittest.mock.Mock()
        db.query.return_value.filter.return_value.first.return_value = user
        db.refresh.side_effect = lambda refreshed: None

        with patch("routes.auth.create_access_token", return_value="signed-token"):
            response = guest_login(
                GuestLoginRequest(
                    name="Current Name",
                    email="ALEX@example.com",
                ),
                db,
            )

        self.assertEqual(user.name, "Current Name")
        self.assertEqual(response["user"]["id"], 17)
        db.add.assert_not_called()
        db.commit.assert_called_once()
