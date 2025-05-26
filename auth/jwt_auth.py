from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Callable, Dict, Tuple

try:
    import jwt
except ImportError as e:  # pragma: no cover - PyJWT missing
    jwt = None


class AuthService:
    """Simple auth service using JWT and email OTP."""

    def __init__(self, jwt_secret: str, otp_sender: Callable[[str, str], None]):
        if not jwt_secret:
            raise ValueError("jwt_secret required")
        if not callable(otp_sender):
            raise ValueError("otp_sender must be callable")
        self.jwt_secret = jwt_secret
        self.otp_sender = otp_sender
        self.otps: Dict[str, Tuple[str, datetime]] = {}

    def generate_otp(self, email: str) -> str:
        """Generate a 6 digit OTP and send via otp_sender."""
        if not email:
            raise ValueError("email required")
        code = f"{random.randint(0, 999999):06d}"
        expiry = datetime.utcnow() + timedelta(minutes=5)
        self.otps[email] = (code, expiry)
        self.otp_sender(email, code)
        return code

    def verify_otp(self, email: str, code: str) -> bool:
        """Verify provided OTP code."""
        if not email or not code:
            raise ValueError("email and code required")
        entry = self.otps.get(email)
        if not entry:
            raise ValueError("OTP not found")
        stored_code, expiry = entry
        if datetime.utcnow() > expiry:
            del self.otps[email]
            raise ValueError("OTP expired")
        if stored_code != code:
            raise ValueError("Invalid OTP")
        del self.otps[email]
        return True

    def create_access_token(self, user_id: str) -> str:
        if not jwt:
            raise RuntimeError("PyJWT is required")
        if not user_id:
            raise ValueError("user_id required")
        payload = {
            "sub": user_id,
            "exp": datetime.utcnow() + timedelta(minutes=15),
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")

    def verify_access_token(self, token: str) -> dict:
        if not jwt:
            raise RuntimeError("PyJWT is required")
        if not token:
            raise ValueError("token required")
        return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
