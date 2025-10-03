from pydantic import BaseModel, Field, ConfigDict, HttpUrl, computed_field
from uuid import UUID
from datetime import datetime
from app.menu.model import PizzaCategory, ToppingCategory
from decimal import Decimal


# Topping Schemas


class ToppingBase(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the topping",
        examples=["Pepperoni", "Fresh Mozzarella", "Bell Peppers", "Italian Sausage"],
    )
    price: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
        description="Additional price for this topping",
        examples=[2.50, 1.75, 0.00, 3.25],
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
    is_vegetarian: bool = Field(
        default=True,
        description="Whether this topping is suitable for vegetarians",
    )
    is_available: bool = Field(
        default=True,
        description="Whether this topping is currently available for ordering",
    )
    image_url: HttpUrl | None = Field(
        default=None,
        max_length=500,
        description="URL to image of the topping",
    )


class ToppingCreate(ToppingBase):
    pass


class ToppingUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    price: Decimal | None = Field(
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
    is_vegetarian: bool | None = None
    is_available: bool | None = None
    image_url: HttpUrl | None = Field(
        default=None,
        max_length=500,
    )


class ToppingResponse(ToppingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Size schemas


class SizeBase(BaseModel):
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
    multiplier: float = Field(
        gt=0,
        default=1.0,
        description="Price multiplier applied to base pizza price",
        examples=[0.85, 1.0, 1.35, 1.65],
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


class SizeUpdate(BaseModel):
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
    multiplier: float | None = Field(
        default=None,
        gt=0,
    )
    is_available: bool | None = None
    sort_order: int | None = Field(
        default=None,
        ge=0,
    )


class SizeResponse(SizeBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Crust schemas


class CrustBase(BaseModel):
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
    additional_price: Decimal = Field(
        ge=0,
        max_digits=6,
        decimal_places=2,
        description="Additional cost for this crust type",
        examples=[2.50, 3.75],
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


class CrustUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    additional_price: Decimal | None = Field(
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
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# Pizza Schemas


class PizzaBase(BaseModel):
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
            "Classic Italian pizza with fresh mozzarella, tomato sauce, and basil",
            "Loaded with pepperoni, Italian sausage, bell peppers, and extra cheese",
        ],
    )
    base_price: Decimal = Field(
        gt=0,
        max_digits=10,
        decimal_places=2,
        description="Base price for regular size pizza",
        examples=[12.99, 18.50, 24.75],
    )
    image_url: HttpUrl | None = Field(
        default=None,
        max_length=500,
        description="URL to pizza image",
    )
    is_available: bool = Field(
        default=True,
        description="Whether the pizza is currently available",
    )
    category: PizzaCategory = Field(
        description="Pizza category", examples=["VEG", "NON_VEG"]
    )


class PizzaCreate(PizzaBase):
    default_topping_ids: list[UUID] | None = Field(
        default=None,
        description="List of topping IDs that come as defaults with this pizza",
    )


class PizzaUpdate(BaseModel):
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
    image_url: HttpUrl | None = Field(
        default=None,
        max_length=500,
    )
    is_available: bool | None = None
    featured: bool | None = None
    category: PizzaCategory | None = None
    default_topping_ids: list[UUID] | None = None


class PizzaResponse(PizzaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    featured: bool
    default_toppings: list[ToppingResponse] = Field(
        default=[],
        description="List of toppings that come standard with this pizza",
    )
    created_at: datetime
    updated_at: datetime


class PaginatedPizzaResponse(BaseModel):
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
