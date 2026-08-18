from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field

from app.core.base_schema import BaseSchema


class StoreConfigBase(BaseSchema):
    name: str
    phone_number: str
    address: str
    is_accepting_orders: bool
    max_delivery_km: float
    min_order_value: Decimal
    latitude: float
    longitude: float


class StoreConfigResponse(StoreConfigBase):
    id: UUID
    base_delivery_fee: Decimal
    tax_rate: Decimal
    per_km_fee: Decimal
    created_at: datetime
    updated_at: datetime


class StoreConfigResponsePublic(StoreConfigBase):
    pass


class StoreConfigUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    phone_number: str | None = Field(
        default=None,
        min_length=10,
        max_length=20,
    )
    address: str | None = Field(
        default=None,
        max_length=255,
    )
    latitude: float | None = Field(
        default=None,
        ge=-90,
        le=90,
    )
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
    )
    max_delivery_km: float | None = Field(
        default=None,
        ge=0,
    )
    is_accepting_orders: bool | None = None
    min_order_value: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    base_delivery_fee: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
    tax_rate: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=4,
    )
    per_km_fee: Decimal | None = Field(
        default=None,
        ge=0,
        decimal_places=2,
    )
