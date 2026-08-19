from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, computed_field

from app.core.base_schema import BaseSchema
from app.menu.schema import CrustResponse, PizzaResponse, SizeResponse, ToppingResponse


class CartItemBase(BaseSchema):
    quantity: int = Field(ge=1, le=99)


class CartItemCreate(CartItemBase):
    pizza_id: UUID
    size_id: UUID
    crust_id: UUID
    topping_ids: list[UUID] | None = None


class CartItemResponse(CartItemBase):
    id: UUID
    total: Decimal
    unit_price: Decimal
    pizza: PizzaResponse
    size: SizeResponse
    crust: CrustResponse
    toppings: list[ToppingResponse]
    created_at: datetime
    updated_at: datetime


class CartItemUpdate(CartItemBase):
    pass


class CartResponse(BaseSchema):
    id: UUID
    subtotal: Decimal
    tax: Decimal
    delivery_charge: Decimal
    total: Decimal
    cart_items: list[CartItemResponse]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.cart_items)
