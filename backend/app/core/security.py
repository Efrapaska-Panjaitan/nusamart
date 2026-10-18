from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jwt.exceptions import InvalidTokenError

from app.core.config import get_settings

ALGORITHM = "HS256"
password_hasher = PasswordHasher()  # Argon2id with library-recommended parameters

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return password_hasher.verify(hashed_password, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False

def create_access_token(user_id: UUID, role: str) -> str:
    settings = get_settings()
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "type": "access", "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except InvalidTokenError as exc:
        raise ValueError("Token tidak valid atau kedaluwarsa") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise ValueError("Token bukan access token")
    return payload
