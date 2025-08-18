from pydantic import BaseModel, Field, ConfigDict, HttpUrl
from uuid import UUID
from datetime import datetime
from app.menu.model import PizzaCategory, ToppingCategory


# Topping Schemas


class ToppingBase(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="name of topping")
    price: float = Field(ge=0, description="topping price")
    description: str | None = None
    category: ToppingCategory
    is_vegetarian: bool = True
    is_available: bool = True
    image_url: HttpUrl | None = Field(default=None, max_length=500)


class ToppingCreate(ToppingBase):
    pass


class ToppingUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    price: float | None = Field(default=None, ge=0)
    description: str | None = None
    category: ToppingCategory | None = None
    is_vegetarian: bool | None = None
    is_available: bool | None = None
    image_url: HttpUrl | None = Field(default=None, max_length=500)


class ToppingResponse(ToppingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Size schemas


class SizeBase(BaseModel):
    name: str = Field(max_length=50)
    display_name: str = Field(max_length=100)
    multiplier: float = Field(gt=0, default=1.0)
    is_available: bool = True
    sort_order: int = 0


class SizeCreate(SizeBase):
    pass


class SizeUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)
    multiplier: float | None = Field(default=None, gt=0)
    is_available: bool | None = None
    sort_order: int | None = None


class SizeResponse(SizeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Crust schemas


class CrustBase(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None
    additional_price: float = Field(default=0.0, ge=0)
    is_available: bool = True
    sort_order: int = 0


class CrustCreate(CrustBase):
    pass


class CrustUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = None
    additional_price: float | None = Field(default=None, ge=0)
    is_available: bool | None = None
    sort_order: int | None = None


class CrustResponse(CrustBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Pizza Schemas


class PizzaBase(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="name of pizza")
    description: str
    base_price: float = Field(gt=0, description="Base price for regular size pizza")
    image_url: HttpUrl | None = Field(default=None, max_length=500)
    is_available: bool = True
    category: PizzaCategory


class PizzaCreate(PizzaBase):
    default_topping_ids: list[UUID] | None = None


class PizzaUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    base_price: float | None = Field(
        default=None,
        gt=0,
    )
    image_url: HttpUrl | None = Field(default=None, max_length=500)
    is_available: bool | None = None
    category: PizzaCategory | None = None
    default_topping_ids: list[UUID] | None = None


class PizzaResponse(PizzaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    default_toppings: list[ToppingResponse] = []
    created_at: datetime
    updated_at: datetime
