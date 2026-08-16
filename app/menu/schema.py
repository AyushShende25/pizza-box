from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, computed_field

from app.core.base_schema import BaseSchema
from app.menu.model import FoodType, ToppingCategory


class PaginationParams(BaseSchema):
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")


class SortablePaginationParams(PaginationParams):
    sort_by: str = Field(
        default="created_at",
        description="Sort field (e.g., 'created_at','name')",
    )
    order: Literal["asc", "desc"] = "desc"


# Topping Schemas


class ToppingQueryParams(BaseSchema):
    category: ToppingCategory | None = Field(
        default=None,
        description="Filter by topping category (meat, cheese, vegetable, etc.)",
    )
    food_type: FoodType | None = Field(
        default=None,
        description="Filter by food type",
    )
    is_available: bool | None = Field(
        default=None, description="Filter by availability"
    )


class ToppingBase(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the topping",
        examples=["Pepperoni", "Fresh Mozzarella", "Bell Peppers", "Italian Sausage"],
    )
    price_modifier: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Detailed description of the topping",
        examples=[
            "Spicy cured Italian sausage slices",
            "Fresh mozzarella cheese made daily",
            "Organic bell peppers, locally sourced",
        ],
    )
    category: ToppingCategory = Field(
        description="Category classification for the topping",
        examples=["MEAT", "CHEESE", "VEGETABLE", "SAUCE"],
    )
    food_type: FoodType = Field(
        description="Food type",
        examples=["VEG", "NON_VEG"],
    )
    is_available: bool = Field(
        default=True,
        description="Whether this topping is currently available for ordering",
    )
    image_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to image of the topping",
    )


class ToppingCreate(ToppingBase):
    pass


class ToppingUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    price_modifier: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    category: ToppingCategory | None = None
    food_type: FoodType | None = None
    is_available: bool | None = None
    image_url: str | None = Field(
        default=None,
        max_length=500,
    )


class ToppingResponse(ToppingBase):
    id: UUID
    created_at: datetime


# Size schemas


class SizeQueryParams(BaseSchema):
    is_available: bool | None = None


class SizeBase(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=50,
        description="Internal name for the size (used in system)",
        examples=["small", "medium", "large", "xl"],
    )
    display_name: str = Field(
        min_length=1,
        max_length=100,
        description="Display name shown to customers",
        examples=['Small (10")', 'Medium (12")', 'Large (14")', 'Extra Large (16")'],
    )
    price_modifier: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    is_available: bool = Field(
        default=True,
        description="Whether this size is currently available for ordering",
    )
    sort_order: int = Field(
        default=0,
        ge=0,
        description="Display order (lower numbers appear first)",
        examples=[1, 2, 3, 4],
    )


class SizeCreate(SizeBase):
    pass


class SizeUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    display_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    price_modifier: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    is_available: bool | None = None
    sort_order: int | None = Field(
        default=None,
        ge=0,
    )


class SizeResponse(SizeBase):
    id: UUID
    created_at: datetime


# Crust schemas


class CrustQueryParams(BaseSchema):
    is_available: bool | None = None


class CrustBase(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the crust type",
        examples=["Thin Crust", "Stuffed Crust"],
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Detailed description of the crust",
        examples=[
            "Crispy thin crust baked to golden perfection",
            "Hand-tossed thick crust with herbs and garlic",
        ],
    )
    price_modifier: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    is_available: bool = Field(
        default=True,
        description="Whether this crust is currently available",
    )
    sort_order: int = Field(
        default=0,
        ge=0,
        description="Display order (lower numbers appear first)",
    )


class CrustCreate(CrustBase):
    pass


class CrustUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    price_modifier: Decimal | None = Field(
        default=None,
        ge=0,
        max_digits=6,
        decimal_places=2,
    )
    is_available: bool | None = None
    sort_order: int | None = Field(
        default=None,
        ge=0,
    )


class CrustResponse(CrustBase):
    id: UUID
    created_at: datetime


# Pizza Schemas

PizzaSortField = Literal[
    "created_at",
    "is_available",
    "is_featured",
    "name",
    "base_price",
    "food_type",
]

SortOrder = Literal["asc", "desc"]


class PizzaBase(BaseSchema):
    name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the pizza",
        examples=["Margherita", "Pepperoni Supreme"],
    )
    description: str = Field(
        min_length=1,
        max_length=1000,
        description="Detailed description of the pizza",
        examples=[
            "Classic Italian pizza with fresh mozzarella, tomato sauce, and basil"
        ],
    )
    base_price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Base price for regular size pizza",
        examples=[12.99, 18.50, 24.75],
    )
    image_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to pizza image",
    )
    is_available: bool = Field(
        default=True,
        description="Whether the pizza is currently available",
    )
    food_type: FoodType = Field(
        description="Food type",
        examples=["VEG", "NON_VEG"],
    )


class PizzaCreate(PizzaBase):
    default_topping_ids: list[UUID] | None = Field(
        default=None,
        description="List of topping IDs that come as defaults with this pizza",
    )


class PizzaUpdate(BaseSchema):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        max_length=1000,
    )
    base_price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2,
    )
    image_url: str | None = Field(
        default=None,
        max_length=500,
        description="URL to pizza image",
    )
    is_available: bool | None = None
    is_featured: bool | None = None
    food_type: FoodType | None = None
    default_topping_ids: list[UUID] | None = None


class PizzaResponse(PizzaBase):
    id: UUID
    is_featured: bool
    default_toppings: list[ToppingResponse] = Field(
        default_factory=list,
        description="List of toppings that come standard with this pizza",
    )
    created_at: datetime
    updated_at: datetime


class PizzaQueryParams(PaginationParams):
    name: str | None = Field(
        default=None,
        description="Filter by pizza name (partial match supported)",
    )
    food_type: FoodType | None = Field(
        default=None,
        description="Filter by food type (veg | non_veg)",
    )
    is_available: bool | None = Field(
        default=None,
        description="Filter by availability",
    )
    is_featured: bool | None = Field(
        default=None,
        description="Filter by featured pizzas",
    )
    sort_by: PizzaSortField = Field(
        default="created_at",
        description="Sort field (e.g., 'created_at','name')",
    )
    order: SortOrder = "desc"


class PaginatedPizzaResponse(BaseSchema):
    total: int = Field(ge=0, description="Total number of pizzas")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    items: list[PizzaResponse] = Field(description="List of pizzas")

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1
