from datetime import date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import Field, computed_field

from app.core.base_schema import BaseSchema
from app.orders.model import OrderStatus, PaymentMethod, PaymentStatus


class OrderItemToppingResponse(BaseSchema):
    id: UUID
    topping_name: str
    topping_price: Decimal


class OrderItemBase(BaseSchema):
    quantity: int = Field(gt=0, le=50, description="Quantity must be between 1 and 50")


class OrderItemCreate(OrderItemBase):
    pizza_id: UUID
    size_id: UUID
    crust_id: UUID
    toppings_ids: list[UUID] | None = None


class OrderItemResponse(OrderItemBase):
    id: UUID
    toppings: list[OrderItemToppingResponse] = Field(default_factory=list)
    pizza_name: str
    size_name: str
    crust_name: str
    size_price_modifier: Decimal
    crust_price_modifier: Decimal
    base_pizza_price: Decimal
    toppings_total_price: Decimal
    unit_price: Decimal
    total_price: Decimal


class OrderBase(BaseSchema):
    notes: str | None = None
    payment_method: PaymentMethod = PaymentMethod.DIGITAL


class OrderCreate(OrderBase):
    address_id: UUID


class OrderUpdate(BaseSchema):
    order_status: OrderStatus


class OrderResponse(OrderBase):
    id: UUID
    order_no: str
    order_items: list[OrderItemResponse] = Field(default_factory=list)
    user_id: UUID
    customer_name: str
    order_status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal
    tax: Decimal
    delivery_charge: Decimal
    total: Decimal
    delivery_name: str
    delivery_phone: str
    delivery_street: str
    delivery_city: str
    delivery_state: str
    delivery_postal_code: str
    delivery_country: str
    created_at: datetime
    updated_at: datetime


class PaginatedOrderResponse(BaseSchema):
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


class BaseOrderQueryParams(BaseSchema):
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=10, ge=1, le=100, description="Items per page")
    order_status: OrderStatus | None = Field(
        default=None, description="Filter by order status"
    )
    payment_status: PaymentStatus | None = Field(
        default=None, description="Filter by payment status"
    )
    payment_method: PaymentMethod | None = Field(
        default=None, description="Filter by payment method"
    )


class UserOrderQueryParams(BaseOrderQueryParams):
    pass


OrderSortField = Literal[
    "created_at",
    "order_no",
    "total",
]

SortOrder = Literal["asc", "desc"]


class AdminOrderQueryParams(BaseOrderQueryParams):
    sort_by: OrderSortField = Field(
        default="created_at",
        description="Sort field (e.g., 'order_no')",
    )
    sort_order: SortOrder = "desc"


class OrderStatsQueryParams(BaseSchema):
    start_date: date
    end_date: date
    limit: int | None = None


class OrderMonthlySalesQueryParams(BaseSchema):
    months_count: int
