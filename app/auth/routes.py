from fastapi import APIRouter, status, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.core.database import SessionDep
from app.core.redis import RedisDep
from app.auth.service import AuthService
from app.auth.schema import (
    UserCreate,
    RegistrationResponse,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse,
    UserEmail,
    UserPassword,
)
from app.auth.dependencies import CurrentUserDep
from app.core.config import settings
from app.core.exceptions import InvalidRefreshTokenError

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
async def register(user_data: UserCreate, session: SessionDep, redis: RedisDep):
    """Register a new user"""
    user = await AuthService(session, redis).create_user(user_data)
    return {
        "message": "user registered successfully, verify your email",
        "user": user,
    }


@auth_router.get("/verify-email")
async def verify_email(session: SessionDep, redis: RedisDep, token: str):
    """Verify user account"""
    return await AuthService(session, redis).verify(token)


@auth_router.post("/login")
async def login(user_credentials: UserLogin, session: SessionDep, redis: RedisDep):
    """User login"""
    auth_service = AuthService(session, redis)

    user = await auth_service.authenticate_user(user_credentials)

    access_token, refresh_token = await auth_service.generate_tokens(user)

    response = JSONResponse(
        content={
            "message": "Login successful",
            "user": {
                "id": str(user.id),
                "email": user.email,
            },
        }
    )
    response.set_cookie(
        "access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


# OAuth2 compatible login for Swagger UI
@auth_router.post("/token", response_model=TokenResponse)
async def login_for_access_token(
    session: SessionDep,
    redis: RedisDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    """OAuth2 compatible token endpoint for Swagger UI"""
    user_credentials = UserLogin(email=form_data.username, password=form_data.password)
    auth_service = AuthService(session, redis)
    user = await auth_service.authenticate_user(user_credentials)

    access_token, refresh_token = await auth_service.generate_tokens(user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    request: Request,
    session: SessionDep,
    redis: RedisDep,
    refresh_request: RefreshTokenRequest | None = None,
):
    """Refresh access token"""
    refresh_token = None
    if refresh_request and refresh_request.refresh_token:
        refresh_token = refresh_request.refresh_token
    else:
        refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise InvalidRefreshTokenError()

    access_token, new_refresh_token = await AuthService(session, redis).refresh_tokens(
        refresh_token
    )

    response = JSONResponse(
        content={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
    )
    response.set_cookie(
        "access_token",
        value=access_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        "refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return response


@auth_router.post("/logout")
async def logout(
    request: Request, session: SessionDep, redis: RedisDep, current_user: CurrentUserDep
):
    """User logout"""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        await AuthService(session, redis).logout_user(refresh_token)

    response = JSONResponse(content={"message": "Logged out successfully"})

    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return response


@auth_router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUserDep):
    """Get current user information"""
    return current_user


@auth_router.post("/resend-verification")
async def resend_verification(
    body: UserEmail,
    session: SessionDep,
    redis: RedisDep,
):
    """Resend verification token"""
    return await AuthService(session, redis).resend_verification_token(body.email)


@auth_router.post("/forgot-password")
async def forgot_password(body: UserEmail, session: SessionDep, redis: RedisDep):
    """Forgot password"""
    return await AuthService(session, redis).forgot_pwd(body.email)


@auth_router.post("/reset-password")
async def reset_password(
    token: str,
    body: UserPassword,
    session: SessionDep,
    redis: RedisDep,
):
    """Reset password"""
    return await AuthService(session, redis).reset_pwd(token, body.password)
