import secrets
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.auth.schema import (
    CreateTokenResponse,
    JwtTokenType,
    TokenPayload,
)
from app.core.config import settings

password_hash = PasswordHash.recommended()


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(password=plain_password, hash=hashed_password)


def create_token(
    sub: str,
    payload: dict | None = None,
    expires_delta: timedelta | None = None,
    refresh: bool = False,
) -> CreateTokenResponse:
    token_type = "refresh" if refresh else "access"

    default_expiry = (
        timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
        if refresh
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    jti = str(uuid4())

    to_encode = {
        **(payload or {}),
        "sub": sub,
        "type": token_type,
        "jti": jti,
        "exp": datetime.now(UTC) + (expires_delta or default_expiry),
    }

    encoded_token = jwt.encode(
        to_encode,
        key=settings.JWT_SECRET_KEY.get_secret_value(),
        algorithm=settings.JWT_ALGORITHM,
    )
    return CreateTokenResponse(token=encoded_token, jti=jti)


def verify_token(
    token: str,
    expected_type: JwtTokenType = "access",
) -> TokenPayload | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["exp", "sub", "type", "jti"]},
        )
        if payload.get("type") != expected_type:
            return None
        return TokenPayload(**payload)
    except jwt.InvalidTokenError:
        return None


def generate_urlsafe_token() -> str:
    return secrets.token_urlsafe(32)
