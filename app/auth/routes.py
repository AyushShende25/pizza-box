from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from app.core.database import SessionDep
from app.core.redis import RedisDep
from app.auth.service import AuthService
from app.auth.schema import UserCreate, RegistrationResponse, UserLogin, TokenResponse
from app.auth.dependencies import FastMailDep
from app.core.config import settings

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=RegistrationResponse,
)
async def register(
    user_data: UserCreate, session: SessionDep, redis: RedisDep, mail_dep: FastMailDep
):
    """Register a new user"""
    user = await AuthService(session, redis, mail_dep).create_user(user_data)
    return {
        "message": "user registered successfully, verify your email",
        "user": user,
    }


@auth_router.get("/verify-email")
async def verify_email(
    session: SessionDep, redis: RedisDep, mail_dep: FastMailDep, token: str
):
    """Verify user account"""
    await AuthService(session, redis, mail_dep).verify(token)
    return {"message": "user account verified successfully"}


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


@auth_router.post("/refresh")
async def refresh_tokens():
    """Refresh access token"""
    pass


@auth_router.post("/logout")
async def logout():
    """User logout"""
    pass


@auth_router.get("/me")
async def get_me():
    """Get current user information"""
    pass
