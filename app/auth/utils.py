from passlib.context import CryptContext
from datetime import timedelta, datetime, timezone
from uuid import uuid4
import jwt
import secrets
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hash=hashed_password)


def create_token(
    sub: str,
    payload: dict | None = None,
    expiry: timedelta | None = None,
    refresh: bool = False,
) -> tuple[str, dict]:
    encode = {
        **(payload or {}),
        "sub": sub,
        "exp": datetime.now(timezone.utc)
        + (expiry or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        "jti": str(uuid4()),
        "refresh": refresh,
    }

    token = jwt.encode(encode, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    return token, encode


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, [settings.JWT_ALGORITHM])
    except jwt.PyJWTError:
        return None


def generate_verification_token() -> str:
    return secrets.token_urlsafe(32)
