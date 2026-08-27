import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.auth.model import UserRole
from app.core.base_schema import BaseSchema


class UserBase(BaseSchema):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=50, description="user first name")
    last_name: str = Field(min_length=1, max_length=50, description="user last name")


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=255, description="password")


class UserLogin(BaseSchema):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: uuid.UUID
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    role: UserRole


class MessageResponse(BaseSchema):
    message: str


class RegistrationResponse(BaseSchema):
    message: str
    user: UserResponse


# Importing from basechema causes a bug since the oauth endpoint expects in snake_case and baseschema modifies to camelCase
class LoginResponse(BaseModel):
    class UserInfo(BaseModel):
        id: uuid.UUID
        email: EmailStr

    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseSchema):
    refresh_token: str | None = None


class UserEmail(BaseSchema):
    email: EmailStr


class UserPassword(BaseSchema):
    password: str


class TokenPayload(BaseSchema):
    sub: str
    jti: str
    type: str
    exp: int


class CreateTokenResponse(BaseSchema):
    token: str
    jti: str


JwtTokenType = Literal["access", "refresh"]

MailTokenType = Literal["reset", "verification"]
