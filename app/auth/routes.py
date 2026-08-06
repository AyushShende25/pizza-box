from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Query, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.auth.dependencies import AuthServiceDep, CurrentUserDep
from app.auth.schema import (
    LoginResponse,
    MessageResponse,
    RefreshTokenRequest,
    RegistrationResponse,
    TokenResponse,
    UserCreate,
    UserEmail,
    UserLogin,
    UserPassword,
    UserResponse,
)
from app.auth.token_store import AuthRedisRepositoryDep
from app.core.config import settings
from app.core.exceptions import BadRequestError

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
async def register(
    input: UserCreate,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
):
    """Register a new user"""
    user = await auth_service.create_user(
        input=input,
        token_store=token_store,
    )
    return {
        "message": "User registered successfully, please verify your email.",
        "user": user,
    }


@auth_router.get(
    "/verify-email",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def verify_email(
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
    token: Annotated[str, Query(description="Verification token sent to email")],
    email: Annotated[str | None, Query()] = None,
):
    """Verify user account"""
    await auth_service.verify_mail(
        token=token,
        token_store=token_store,
    )
    return {"message": "User account verified successfully."}


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    response_model=LoginResponse,
)
async def login(
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    input: UserLogin | None = None,
):
    """User login"""
    email = None
    password = None

    if form_data and form_data.username:
        email = form_data.username
        password = form_data.password
    elif input:
        email = input.email
        password = input.password

    if not email or not password:
        raise BadRequestError(
            error_code="MISSING_CREDENTIALS",
            message="Email and password required",
        )

    user = await auth_service.authenticate_user(
        input=UserLogin(email=email, password=password)
    )

    access_token, refresh_token = await auth_service.generate_tokens(
        user=user,
        token_store=token_store,
    )

    response.set_cookie(
        "access_token",
        value=access_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_HOURS * 60 * 60,
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
        },
    }


@auth_router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    response_model=TokenResponse,
)
async def refresh_tokens(
    response: Response,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
    refresh_request: RefreshTokenRequest | None = None,
):
    """Refresh access token (supports HTTP-only cookie or JSON body for Swagger UI testing)."""
    refresh_token = refresh_token_cookie or (
        refresh_request.refresh_token if refresh_request else None
    )
    if not refresh_token:
        raise BadRequestError(
            message="Refresh token missing from request body or cookies",
            error_code="MISSING_REFRESH_TOKEN",
        )

    new_access_token, new_refresh_token = await auth_service.refresh_tokens(
        refresh_token=refresh_token,
        token_store=token_store,
    )

    response.set_cookie(
        "access_token",
        value=new_access_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_HOURS * 60 * 60,
    )

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def logout(
    response: Response,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
    refresh_token: Annotated[str | None, Cookie(alias="refresh_token")] = None,
):
    """User logout"""
    if refresh_token:
        await auth_service.logout_user(
            refresh_token=refresh_token,
            token_store=token_store,
        )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )

    return {"message": "Logged out successfully"}


@auth_router.post(
    "/logout-all",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def logout_all(
    response: Response,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
    current_user: CurrentUserDep,
):
    """Logout user from all devices and revoke all refresh tokens."""
    await auth_service.logout_user_all(
        user_id=str(current_user.id),
        token_store=token_store,
    )

    response.delete_cookie(
        key="access_token",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )

    return {"message": "Logged out from all devices successfully"}


@auth_router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserResponse,
)
async def get_me(current_user: CurrentUserDep):
    """Get current user information"""
    return current_user


@auth_router.post(
    "/resend-verification",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def resend_verification(
    input: UserEmail,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
):
    """Resend verification token"""
    await auth_service.resend_verification_token(
        email=input.email,
        token_store=token_store,
    )
    return {
        "message": "If this email is registered and unverified, a verification email has been sent."
    }


@auth_router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def forgot_password(
    input: UserEmail,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
):
    """Forgot password"""
    await auth_service.forgot_password(
        email=input.email,
        token_store=token_store,
    )
    return {
        "message": f"If an account with {input.email} exists, a reset link has been sent."
    }


@auth_router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
async def reset_password(
    token: str,
    input: UserPassword,
    auth_service: AuthServiceDep,
    token_store: AuthRedisRepositoryDep,
):
    """Reset password"""
    await auth_service.reset_password(
        token=token, password=input.password, token_store=token_store
    )
    return {"message": "Password reset successful."}
