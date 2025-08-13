from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import timedelta
from app.auth.schema import UserCreate, UserLogin
from app.auth.model import User
from app.auth.utils import (
    get_password_hash,
    generate_urlsafe_token,
    verify_password,
    create_token,
    decode_token,
)
from app.core.config import settings
from app.core.redis import RedisService
from app.utils.templates.email_templates import (
    verification_email_html,
    welcome_email_html,
    forgot_password_email_html,
    password_reset_confirmation_email_html,
)
from app.workers.email_tasks import send_mail_task


class AuthService:
    """Service class for authentication operations."""

    def __init__(
        self,
        session: AsyncSession,
        redis: RedisService,
    ):
        self.session = session
        self.redis = redis

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

        await self._send_verification_email(user)
        return user

    async def verify(self, token: str):
        user_id = await self.redis.verify_token(token=token, token_type="verification")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid or expired token",
            )

        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user does not exist",
            )

        user.is_verified = True
        await self.session.commit()
        await self.session.refresh(user)

        await self.redis.delete_token(token, token_type="verification")

        send_mail_task.delay(
            recipients=[user.email],
            subject="welcome to pizza-box",
            body=welcome_email_html(user),
        )
        return {"message": "user account verified successfully"}

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
        await self.redis.store_refresh_jti(
            refresh_jti,
            str(user.id),
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

        token_valid = await self.redis.validate_refresh_jti(refresh_jti, user_id)
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

        # Delete the old refresh-token-id from redis
        await self.redis.revoke_refresh_jti(refresh_jti)

        return await self.generate_tokens(user)

    async def logout_user(self, refresh_token: str):
        payload = decode_token(refresh_token)
        if payload and payload.get("refresh"):
            refresh_jti = payload.get("jti")
            if refresh_jti:
                # Remove refresh token-id from Redis
                await self.redis.revoke_refresh_jti(refresh_jti)

    async def resend_verification_token(self, email: str):
        user = await self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with this email does not exist, please register",
            )
        if user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already verified",
            )

        await self._send_verification_email(user)

        return {"message": "Verification email resent successfully"}

    async def _send_verification_email(self, user: User):
        verification_token = generate_urlsafe_token()

        await self.redis.store_token(
            token=verification_token, user_id=str(user.id), token_type="verification"
        )
        # Send verification email
        link = f"{settings.CLIENT_URL}/verify-email?token={verification_token}"

        send_mail_task.delay(
            recipients=[user.email],
            subject="Verify your email",
            body=verification_email_html(link),
        )
        return True

    async def forgot_pwd(self, email: str):
        user = await self.get_user_by_email(email)
        if not user or not user.is_verified:
            return {
                "message": "If an account with this email exists, you will receive a reset link"
            }

        reset_token = generate_urlsafe_token()

        await self.redis.store_token(
            token=reset_token, user_id=str(user.id), token_type="reset"
        )

        # Send reset email
        link = f"{settings.CLIENT_URL}/reset-password?token={reset_token}"

        send_mail_task.delay(
            recipients=[user.email],
            subject="Reset your password",
            body=forgot_password_email_html(link),
        )

        return {
            "message": "If an account with this email exists, you will receive a reset link"
        }

    async def reset_pwd(self, token: str, password: str):
        user_id = await self.redis.verify_token(token=token, token_type="reset")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="invalid or expired token",
            )
        await self.redis.delete_token(token, token_type="reset")

        user = await self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="user does not exist",
            )

        password_hash = get_password_hash(password)
        user.password_hash = password_hash
        await self.session.commit()
        await self.session.refresh(user)

        # revoke all refresh-tokens-ids for this user
        await self.redis.revoke_all_user_refresh_jtis(str(user.id))

        send_mail_task.delay(
            recipients=[user.email],
            subject="password-reset successful",
            body=password_reset_confirmation_email_html(user),
        )

        return {"message": "password reset successful"}
