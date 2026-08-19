import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Column,
    ForeignKey,
    Integer,
    Table,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.auth.model import User
    from app.menu.model import Crust, Pizza, Size, Topping


cart_item_topping = Table(
    "cart_item_topping",
    Base.metadata,
    Column(
        "cart_item_id",
        Uuid(as_uuid=True),
        ForeignKey("cart_items.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topping_id",
        Uuid(as_uuid=True),
        ForeignKey("toppings.id", ondelete="RESTRICT"),
        primary_key=True,
    ),
)


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    unit_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    total: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )

    cart_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE")
    )
    cart: Mapped["Cart"] = relationship(back_populates="cart_items")

    pizza_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pizzas.id", ondelete="RESTRICT")
    )
    pizza: Mapped["Pizza"] = relationship()

    size_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sizes.id", ondelete="RESTRICT")
    )
    size: Mapped["Size"] = relationship()

    crust_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("crusts.id", ondelete="RESTRICT")
    )
    crust: Mapped["Crust"] = relationship()

    toppings: Mapped[list["Topping"]] = relationship(
        secondary=cart_item_topping,
        back_populates="cart_items",
    )
    toppings_total_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
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

    def __repr__(self):
        return f"<CartItem(id={self.id})>"


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    subtotal: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    tax: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    delivery_charge: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    total: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped["User"] = relationship()

    cart_items: Mapped[list["CartItem"]] = relationship(
        back_populates="cart",
        cascade="all, delete-orphan",
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

    def __repr__(self):
        return f"<Cart(id={self.id})>"
