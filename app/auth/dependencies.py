from typing import Annotated

from fastapi import (
    Cookie,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param

from app.auth.model import User, UserRole
from app.auth.service import AuthService
from app.auth.utils import verify_token
from app.core.database import AsyncSessionLocal, SessionDep
from app.core.exceptions import (
    AuthenticationError,
    EntityNotFoundError,
)
from app.libs.fastmail import FastMailService


def get_mail_service() -> FastMailService:
    """Dependency provider for MailService."""
    return FastMailService()


FastMailDep = Annotated[FastMailService, Depends(get_mail_service)]


def get_auth_service(session: SessionDep) -> AuthService:
    """Provides a fresh AuthService instance"""
    return AuthService(session)


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request) -> str | None:
        token = None
        auth_header = request.headers.get("Authorization")

        if auth_header:
            scheme, param = get_authorization_scheme_param(auth_header)
            if scheme.lower() == "bearer":
                token = param
        if not token:
            token = request.cookies.get("access_token")
        if not token:
            if self.auto_error:
                raise AuthenticationError(
                    message="Not authenticated",
                    error_code="MISSING_TOKEN",
                )
            return None

        return token


oauth2_scheme = OAuth2PasswordBearerWithCookie(
    tokenUrl="/api/v1/auth/login", auto_error=False
)


async def get_current_user(
    session: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    if not token:
        raise AuthenticationError(
            error_code="MISSING_TOKEN",
            message="Not authenticated",
        )
    payload = verify_token(token)
    if not payload:
        raise AuthenticationError(
            error_code="INVALID_TOKEN",
            message="Invalid or expired token",
        )

    user_id = payload.sub
    if user_id is None:
        raise AuthenticationError(
            error_code="INVALID_TOKEN_STRUCTURE",
            message="Token missing user identifier",
        )

    user = await AuthService(session).get_user_by_id(user_id=user_id)
    if not user:
        raise EntityNotFoundError(
            message="User not found",
            error_code="USER_NOT_FOUND",
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]

oauth2_optional = OAuth2PasswordBearerWithCookie(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
)


async def get_optional_user(
    session: SessionDep,
    token: Annotated[str | None, Depends(oauth2_optional)] = None,
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(session=session, token=token)
    except HTTPException:
        return None


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]


class RoleChecker:
    def __init__(self, allowed_roles: list[UserRole]):
        self.allowed_roles = allowed_roles

    async def __call__(self, current_user: CurrentUserDep):
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to perform this action",
            )
        return current_user


AdminUserDep = Annotated[User, Depends(RoleChecker([UserRole.ADMIN]))]


async def get_current_user_ws(
    websocket: WebSocket,
    token: Annotated[str | None, Cookie(alias="access_token")] = None,
):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    payload = verify_token(token)
    if not payload:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user_id = payload.sub
    if user_id is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    async with AsyncSessionLocal() as session:
        user = await AuthService(session).get_user_by_id(user_id=user_id)
        if not user:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return user


async def get_current_admin_ws(
    websocket: WebSocket,
    token: Annotated[str | None, Cookie(alias="access_token")] = None,
):
    if token is None:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    payload = verify_token(token)
    if not payload:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    user_id = payload.sub

    if not user_id:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    async with AsyncSessionLocal() as session:
        user = await AuthService(session).get_user_by_id(user_id=user_id)
        if not user or user.role != UserRole.ADMIN:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)

    return user
