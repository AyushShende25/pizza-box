from pydantic import Field, computed_field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.menu.schema import PizzaResponse, CrustResponse, SizeResponse, ToppingResponse
from app.core.base_schema import BaseSchema


class CartItemBase(BaseSchema):
    quantity: int = Field(ge=1, le=99)


class CartItemCreate(CartItemBase):
    pizza_id: UUID
    size_id: UUID
    crust_id: UUID
    topping_ids: list[UUID] | None


class CartItemResponse(CartItemBase):
    id: UUID
    total: Decimal
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
