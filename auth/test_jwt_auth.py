import pytest
from datetime import datetime, timedelta

import jwt

from auth.jwt_auth import AuthService


def dummy_sender(email: str, code: str) -> None:
    pass


def test_otp_generation_and_verification():
    service = AuthService("secret", dummy_sender)
    code = service.generate_otp("user@example.com")
    assert service.verify_otp("user@example.com", code) is True


def test_otp_wrong_code():
    service = AuthService("secret", dummy_sender)
    code = service.generate_otp("user@example.com")
    with pytest.raises(ValueError):
        service.verify_otp("user@example.com", "000000")


def test_otp_expired(monkeypatch):
    service = AuthService("secret", dummy_sender)
    code = service.generate_otp("user@example.com")
    # force expiry
    service.otps["user@example.com"] = (code, datetime.utcnow() - timedelta(seconds=1))
    with pytest.raises(ValueError):
        service.verify_otp("user@example.com", code)


def test_token_creation_and_verification():
    service = AuthService("secret", dummy_sender)
    token = service.create_access_token("user1")
    claims = service.verify_access_token(token)
    assert claims["sub"] == "user1"


def test_expired_token():
    service = AuthService("secret", dummy_sender)
    payload = {"sub": "user1", "exp": datetime.utcnow() - timedelta(seconds=1)}
    token = jwt.encode(payload, "secret", algorithm="HS256")
    with pytest.raises(jwt.ExpiredSignatureError):
        service.verify_access_token(token)


def test_invalid_signature():
    service = AuthService("secret", dummy_sender)
    token = service.create_access_token("user1")
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(token, "wrong", algorithms=["HS256"])
