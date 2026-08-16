from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.model import User, UserRole
from app.auth.schema import UserCreate, UserLogin
from app.auth.token_store import AuthRedisRepository
from app.auth.utils import (
    create_token,
    generate_urlsafe_token,
    get_password_hash,
    verify_password,
    verify_token,
)
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    BadRequestError,
    ConflictError,
    EntityNotFoundError,
)
from app.utils.templates.email_templates import (
    forgot_password_email_html,
    password_reset_confirmation_email_html,
    verification_email_html,
    welcome_email_html,
)
from app.workers.email_tasks import send_mail_task


class AuthService:
    """Service class for authentication operations"""

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        data: UserCreate,
        token_store: AuthRedisRepository,
        auto_verify: bool = False,
    ) -> User:
        existing_user = await self.get_user_by_email(data.email)
        if existing_user:
            raise ConflictError(
                error_code="USER_ALREADY_EXISTS",
                message=f"User with {data.email} email already exists",
            )

        password_hash = get_password_hash(data.password)

        user = User(
            email=data.email,
            password_hash=password_hash,
            first_name=data.first_name,
            last_name=data.last_name,
            is_verified=auto_verify,
        )

        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)

        if not auto_verify:
            await self._send_verification_email(user, token_store)
        return user

    async def verify_mail(
        self,
        token: str,
        token_store: AuthRedisRepository,
    ) -> User:
        user_id = await token_store.get_mail_token_user(
            token=token,
            token_type="verification",
        )
        if not user_id:
            raise AuthenticationError(
                error_code="INVALID_TOKEN",
                message="Invalid or expired token",
            )

        user = await self.get_user_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                message=f"User: {user_id} not found",
                error_code="USER_NOT_FOUND",
            )

        user.is_verified = True
        await self.session.commit()
        await self.session.refresh(user)

        await token_store.delete_mail_token(
            token=token,
            token_type="verification",
        )

        send_mail_task.delay(
            recipients=[user.email],
            subject="welcome to pizza-box",
            body=welcome_email_html(user),
        )
        return user

    async def authenticate_user(self, data: UserLogin) -> User:
        user = await self.get_user_by_email(data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise AuthenticationError(
                error_code="INVALID_CREDENTIALS",
                message="Incorrect email or password",
            )
        if not user.is_verified:
            raise AuthenticationError(
                error_code="ACCOUNT_NOT_VERIFIED",
                message="Please verify your account first",
            )
        return user

    async def generate_tokens(
        self,
        user: User,
        token_store: AuthRedisRepository,
    ) -> tuple[str, str]:
        access = create_token(
            sub=str(user.id),
            payload={"email": user.email, "role": user.role.value},
            refresh=False,
        )
        refresh = create_token(
            sub=str(user.id),
            refresh=True,
        )

        # Store in Redis with expiration
        await token_store.create_refresh_session(
            session_id=refresh.jti,
            user_id=str(user.id),
        )

        return access.token, refresh.token

    async def refresh_tokens(
        self,
        refresh_token: str,
        token_store: AuthRedisRepository,
    ) -> tuple[str, str]:
        payload = verify_token(
            token=refresh_token,
            expected_type="refresh",
        )
        if not payload:
            raise AuthenticationError(
                message="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN",
            )

        user_id = payload.sub
        refresh_jti = payload.jti

        if not user_id or not refresh_jti:
            raise AuthenticationError(
                message="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN",
            )

        session_user_id = await token_store.get_refresh_session_user(
            session_id=refresh_jti
        )
        if not session_user_id == user_id:
            raise AuthenticationError(
                message="Invalid refresh token",
                error_code="INVALID_REFRESH_TOKEN",
            )

        user = await self.get_user_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        # Delete the old session-id from redis
        await token_store.delete_refresh_session(session_id=refresh_jti)

        return await self.generate_tokens(user, token_store)

    async def logout_user(
        self,
        refresh_token: str,
        token_store: AuthRedisRepository,
    ) -> None:
        payload = verify_token(
            token=refresh_token,
            expected_type="refresh",
        )
        if payload and payload.type == "refresh" and payload.jti:
            await token_store.delete_refresh_session(session_id=payload.jti)

    async def logout_user_all(
        self,
        user_id: str,
        token_store: AuthRedisRepository,
    ) -> None:
        await token_store.delete_all_refresh_sessions(user_id=user_id)

    async def resend_verification_token(
        self,
        email: str,
        token_store: AuthRedisRepository,
    ) -> None:
        user = await self.get_user_by_email(email)
        if not user:
            return

        if user.is_verified:
            raise BadRequestError(
                error_code="ALREADY_VERIFIED",
                message="User is already verified",
            )

        await self._send_verification_email(user, token_store)

    async def _send_verification_email(
        self,
        user: User,
        token_store: AuthRedisRepository,
    ) -> None:
        verification_token = generate_urlsafe_token()

        await token_store.store_mail_token(
            token=verification_token,
            user_id=str(user.id),
            token_type="verification",
        )

        link = f"{settings.CLIENT_URL}/verify-email?token={verification_token}&email={user.email}"

        send_mail_task.delay(
            recipients=[user.email],
            subject="Verify your email",
            body=verification_email_html(link),
        )

    async def forgot_password(
        self,
        email: str,
        token_store: AuthRedisRepository,
    ) -> None:
        user = await self.get_user_by_email(email)
        if not user or not user.is_verified:
            return

        reset_token = generate_urlsafe_token()

        await token_store.store_mail_token(
            token=reset_token,
            user_id=str(user.id),
            token_type="reset",
        )

        if user.role == UserRole.ADMIN:
            link = f"{settings.ADMIN_URL}/reset-password?token={reset_token}"
        else:
            link = f"{settings.CLIENT_URL}/reset-password?token={reset_token}"

        send_mail_task.delay(
            recipients=[user.email],
            subject="Reset your password",
            body=forgot_password_email_html(link),
        )

    async def reset_password(
        self,
        token: str,
        password: str,
        token_store: AuthRedisRepository,
    ) -> User:
        user_id = await token_store.get_mail_token_user(
            token=token,
            token_type="reset",
        )
        if not user_id:
            raise AuthenticationError(
                error_code="INVALID_TOKEN",
                message="Invalid or expired reset token",
            )

        user = await self.get_user_by_id(user_id)
        if not user:
            raise EntityNotFoundError(
                message="User not found",
                error_code="USER_NOT_FOUND",
            )

        await token_store.delete_mail_token(
            token=token,
            token_type="reset",
        )

        password_hash = get_password_hash(password)
        user.password_hash = password_hash
        await self.session.commit()
        await self.session.refresh(user)

        # revoke all refresh-tokens-ids for this user
        await token_store.delete_all_refresh_sessions(user_id=str(user.id))

        send_mail_task.delay(
            recipients=[user.email],
            subject="Password Reset Successful",
            body=password_reset_confirmation_email_html(user),
        )

        return user
