import uuid
import enum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import Uuid, ForeignKey, TIMESTAMP, func, DECIMAL, Enum, Integer, String
from datetime import datetime
from typing import TYPE_CHECKING
from decimal import Decimal
from app.core.base import Base

if TYPE_CHECKING:
    from app.auth.model import User


class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(enum.Enum):
    COD = "cod"
    CARD = "card"
    UPI = "upi"


class OrderItemTopping(Base):
    __tablename__ = "order_item_topping"
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("order_item.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item: Mapped["OrderItem"] = relationship(back_populates="toppings")

    topping_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("topping.id", ondelete="SET NULL"),
        nullable=True,
    )
    topping_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    topping_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class OrderItem(Base):
    __tablename__ = "order_item"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE")
    )
    order: Mapped["Order"] = relationship(back_populates="order_items")

    pizza_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pizza.id", ondelete="SET NULL"),
        nullable=True,
    )
    size_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("size.id", ondelete="SET NULL"),
        nullable=True,
    )
    crust_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("crust.id", ondelete="SET NULL"),
        nullable=True,
    )
    toppings: Mapped[list["OrderItemTopping"]] = relationship(
        back_populates="order_item",
        cascade="all, delete-orphan",
    )

    pizza_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    size_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    crust_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    size_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    crust_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    base_pizza_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    toppings_total_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    unit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    total_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    order_no: Mapped[str] = mapped_column(
        String(50),
        unique=True,
    )

    subtotal: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    tax: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    delivery_charge: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    order_status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus),
        nullable=False,
        default=OrderStatus.PENDING,
    )
    payment_status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus),
        nullable=False,
        default=PaymentStatus.PENDING,
    )
    payment_method: Mapped[PaymentMethod] = mapped_column(
        Enum(PaymentMethod),
        nullable=False,
        default=PaymentMethod.COD,
    )

    order_items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped["User"] = relationship()

    address_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("addresses.id", ondelete="SET NULL"),
        nullable=True,
    )
    delivery_address: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
