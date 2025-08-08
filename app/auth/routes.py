from fastapi import APIRouter, status
from app.core.database import SessionDep
from app.core.redis import RedisDep
from app.auth.service import AuthService
from app.auth.schema import UserCreate, RegistrationResponse
from app.auth.dependencies import FastMailDep

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


@auth_router.post("/verify-email")
async def verify_email():
    """Verify user account"""
    pass


@auth_router.post("/login")
async def login():
    """User login"""
    pass


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
