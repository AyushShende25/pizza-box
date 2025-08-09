from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import timedelta
from app.auth.schema import UserCreate, UserLogin
from app.auth.model import User
from app.auth.utils import (
    get_password_hash,
    generate_verification_token,
    verify_password,
    create_token,
    decode_token,
)
from app.core.config import settings
from app.core.redis import RedisService
from app.libs.fastmail import FastMailService
from app.utils.templates.mail_verification import (
    verification_email_html,
    welcome_email_html,
)


class AuthService:
    """Service class for authentication operations."""

    def __init__(
        self,
        session: AsyncSession,
        redis: RedisService,
        fast_mail_service: FastMailService | None = None,
    ):
        self.session = session
        self.redis = redis
        self.fast_mail_service = fast_mail_service

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.scalars(stmt)
        return result.first()

    async def get_user_by_id(self, user_id: str) -> User | None:
        user = await self.session.get(User, user_id)
        return user

    async def create_user(self, user_credentials: UserCreate) -> User:
        existing_user = await self.get_user_by_email(user_credentials.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user with that email already exists",
            )

        password_hash = get_password_hash(user_credentials.password)

        user = User(
            email=user_credentials.email,
            password_hash=password_hash,
            first_name=user_credentials.first_name,
            last_name=user_credentials.last_name,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        # generate and store verification token
        verification_token = generate_verification_token()

        await self.redis.store_verification_token(
            token=verification_token,
            user_id=str(user.id),
            expires_in=timedelta(
                seconds=settings.MAIL_VERIFICATION_TOKEN_EXPIRE_SECONDS
            ),
        )
        # Send verification email
        link = f"{settings.CLIENT_URL}/verify-email?token={verification_token}"

        if not self.fast_mail_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="mail service is not configured",
            )

        await self.fast_mail_service.send_mail(
            recipients=[user.email],
            subject="Verify your email",
            body=verification_email_html(link),
        )
        return user

    async def verify(self, token: str):
        user_id = await self.redis.verify_verification_token(token=token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid or expired token",
            )
        await self.redis.delete_verification_token(token)

        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user does not exist",
            )

        user.is_verified = True
        await self.session.commit()
        await self.session.refresh(user)

        if not self.fast_mail_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="mail service is not configured",
            )

        await self.fast_mail_service.send_mail(
            recipients=[user.email],
            subject="welcome to pizza-box",
            body=welcome_email_html(user),
        )
        return True

    async def authenticate_user(self, credentials: UserLogin) -> User:
        user = await self.get_user_by_email(credentials.email)

        if not user or not verify_password(credentials.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="please verify your account first",
            )
        return user

    async def generate_tokens(self, user: User) -> tuple[str, str]:
        access_token, _ = create_token(
            sub=str(user.id),
            payload={
                "email": user.email,
            },
        )
        refresh_token, refresh_payload = create_token(
            sub=str(user.id),
            refresh=True,
            expiry=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        # Store in Redis with expiration
        refresh_jti = refresh_payload["jti"]
        await self.redis.store_refresh_token(
            refresh_jti,
            str(user.id),
            expires_in=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        return access_token, refresh_token

    async def refresh_tokens(self, refresh_token: str) -> tuple[str, str]:
        payload = decode_token(refresh_token)
        if not payload or not payload.get("refresh"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = payload.get("sub")
        refresh_jti = payload.get("jti")
        if not user_id or not refresh_jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token structure",
            )

        token_valid = await self.redis.validate_refresh_token(refresh_jti, user_id)
        if not token_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has been revoked",
            )

        user = await self.session.get(User, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="user not found"
            )

        # Delete the old refresh-token from redis
        await self.redis.revoke_refresh_token(refresh_jti)

        return await self.generate_tokens(user)

    async def logout_user(self, refresh_token: str):
        payload = decode_token(refresh_token)
        if payload and payload.get("refresh"):
            refresh_jti = payload.get("jti")
            if refresh_jti:
                # Remove refresh token from Redis
                await self.redis.revoke_refresh_token(refresh_jti)
