from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.core.base_schema import BaseSchema


class AddressBase(BaseSchema):
    full_name: str = Field(
        min_length=1,
        max_length=100,
        description="Full Name of address owner",
    )
    phone_number: str = Field(
        pattern=r"^\d{10}$",
        description="10 digit phone number without country-code",
    )
    street: str = Field(
        min_length=1,
        max_length=255,
    )
    city: str = Field(
        min_length=1,
        max_length=100,
    )
    state: str = Field(
        min_length=1,
        max_length=100,
    )
    postal_code: str = Field(
        pattern=r"^[1-9]\d{5}$",
        description="6-digit Indian PIN code",
    )
    country: str = Field(
        min_length=1,
        max_length=100,
    )
    is_default: bool = Field(
        default=False,
        description="Make this default address",
    )


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
        pattern=r"^\d{10}$",
        description="10 digit phone number without country-code",
    )
    street: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    city: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    state: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    postal_code: str | None = Field(
        default=None,
        pattern=r"^[1-9]\d{5}$",
        description="6-digit Indian PIN code",
    )
    country: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    is_default: bool | None = None


class AddressResponse(AddressBase):
    id: UUID
    created_at: datetime
    user_id: UUID
