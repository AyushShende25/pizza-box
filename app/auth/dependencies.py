from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import Depends, Request
from typing import Annotated
from app.core.database import SessionDep
from app.auth.utils import decode_token
from app.auth.model import User, UserRole
from app.libs.fastmail import FastMailService
from app.core.exceptions import (
    UserNotFoundError,
    InvalidTokenError,
    AuthenticationError,
    AuthorizationError,
)


def get_mail_service() -> FastMailService:
    """Dependency provider for MailService."""
    return FastMailService()


FastMailDep = Annotated[FastMailService, Depends(get_mail_service)]


class OAuth2PasswordBearerWithCookie(OAuth2PasswordBearer):
    async def __call__(self, request: Request):
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
            else:
                return None
        return token


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
):
    payload = decode_token(token)
    if not payload:
        raise InvalidTokenError()

    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidTokenError(
            message="Token missing user identifier",
            error_code="INVALID_TOKEN_STRUCTURE",
        )

    if payload.get("refresh"):
        raise AuthenticationError(
            message="Refresh token cannot be used for authentication",
            error_code="REFRESH_TOKEN_MISUSE",
        )

    user = await session.get(User, user_id)
    if not user:
        raise UserNotFoundError()
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]

oauth2_optional = OAuth2PasswordBearerWithCookie(
    tokenUrl="/api/v1/auth/token",
    auto_error=False,
)


async def get_optional_user(
    session: SessionDep, token: Annotated[str | None, Depends(oauth2_optional)] = None
) -> User | None:
    if not token:
        return None
    try:
        return await get_current_user(session, token)
    except Exception:
        return None


OptionalUserDep = Annotated[User | None, Depends(get_optional_user)]


class RoleChecker:
    def __init__(self, roles):
        self.roles = roles

    async def __call__(self, current_user: CurrentUserDep):
        if current_user.role not in self.roles:
            raise AuthorizationError()
        return current_user


AdminOnlyDep = Annotated[User, Depends(RoleChecker([UserRole.ADMIN]))]

UserOrAdminDep = Annotated[User, Depends(RoleChecker([UserRole.ADMIN, UserRole.USER]))]
