from fastapi.security import OAuth2PasswordBearer
from fastapi.security.utils import get_authorization_scheme_param
from fastapi import status, HTTPException, Depends, Request
from typing import Annotated
from app.core.database import SessionDep
from app.auth.utils import decode_token
from app.auth.model import User
from app.libs.fastmail import FastMailService


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
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return token


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="unauthorized access",
    )
    payload = decode_token(token)
    if not payload:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    if payload.get("refresh"):
        raise credentials_exception

    user = await session.get(User, user_id)
    if not user:
        raise credentials_exception
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
