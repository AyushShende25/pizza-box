from pydantic import Field, ConfigDict
from uuid import UUID
from datetime import datetime
from app.core.base_schema import BaseSchema


class AddressBase(BaseSchema):
    full_name: str = Field(
        min_length=1,
        max_length=100,
        description="Full Name of address owner",
    )
    phone_number: str = Field(
        min_length=10,
        max_length=10,
        description="10 digit phone number without country-code",
    )
    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    postal_code: str = Field(min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    is_default: bool = Field(default=False, description="Default address")


class AddressCreate(AddressBase):
    pass


class AddressUpdate(BaseSchema):
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Full Name of address owner",
    )
    phone_number: str | None = Field(
        default=None,
        min_length=10,
        max_length=10,
        description="10 digit phone number without country-code",
    )
    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    is_default: bool | None = None


class AddressResponse(AddressBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    user_id: UUID
