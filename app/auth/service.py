from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from datetime import timedelta
from app.auth.schema import UserCreate
from app.auth.model import User
from app.auth.utils import get_password_hash, generate_verification_token
from app.core.config import settings
from app.core.redis import RedisService
from app.libs.fastmail import FastMailService
from app.utils.templates.mail_verification import verification_email_html


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
        link = f"{settings.BASE_URL}/api/v1/auth/verify?token={verification_token}"

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
