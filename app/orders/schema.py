from pydantic import BaseModel, ConfigDict, Field, computed_field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.orders.model import OrderStatus, PaymentStatus, PaymentMethod


class OrderItemToppingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    topping_name: str
    topping_price: Decimal


class OrderItemBase(BaseModel):
    quantity: int = Field(gt=0, le=50, description="Quantity must be between 1 and 50")


class OrderItemCreate(OrderItemBase):
    pizza_id: UUID
    size_id: UUID
    crust_id: UUID
    toppings_ids: list[UUID] | None = None


class OrderItemResponse(OrderItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    toppings: list[OrderItemToppingResponse] = []
    pizza_name: str
    size_name: str
    crust_name: str
    size_price: Decimal
    crust_price: Decimal
    base_pizza_price: Decimal
    toppings_total_price: Decimal
    unit_price: Decimal
    total_price: Decimal


class OrderBase(BaseModel):
    payment_method: PaymentMethod
    notes: str | None = None


class OrderCreate(OrderBase):
    address_id: UUID
    order_items: list[OrderItemCreate]


class OrderUpdate(BaseModel):
    order_status: OrderStatus


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    order_no: str
    order_items: list[OrderItemResponse] = []
    user_id: UUID
    order_status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    tax: Decimal
    delivery_charge: Decimal
    total: Decimal
    delivery_address: str
    created_at: datetime
    updated_at: datetime


class PaginatedOrderResponse(BaseModel):
    total: int = Field(ge=0, description="Total number of orders")
    page: int = Field(ge=1, description="Current page number")
    limit: int = Field(ge=1, le=100, description="Items per page")
    pages: int = Field(ge=0, description="Total number of pages")
    items: list[OrderResponse] = Field(description="List of orders")

    @computed_field
    @property
    def has_next(self) -> bool:
        return self.page < self.pages

    @computed_field
    @property
    def has_prev(self) -> bool:
        return self.page > 1
