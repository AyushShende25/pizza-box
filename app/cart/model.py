from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    Uuid,
    TIMESTAMP,
    func,
    ForeignKey,
    Table,
    Column,
    Integer,
    DECIMAL,
)
from datetime import datetime
import uuid
from app.core.base import Base
from typing import TYPE_CHECKING
from decimal import Decimal

if TYPE_CHECKING:
    from app.menu.model import Pizza, Size, Crust, Topping
    from app.auth.model import User


cart_item_topping = Table(
    "cart_item_topping",
    Base.metadata,
    Column(
        "cart_item_id",
        Uuid(as_uuid=True),
        ForeignKey("cart_item.id"),
        primary_key=True,
    ),
    Column(
        "topping_id",
        Uuid(as_uuid=True),
        ForeignKey("topping.id"),
        primary_key=True,
    ),
)


class CartItem(Base):
    __tablename__ = "cart_item"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    total: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    cart_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cart.id"))
    cart: Mapped["Cart"] = relationship(back_populates="cart_items")
    pizza_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("pizza.id"))
    pizza: Mapped["Pizza"] = relationship()
    size_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("size.id"))
    size: Mapped["Size"] = relationship()
    crust_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("crust.id"))
    crust: Mapped["Crust"] = relationship()

    toppings: Mapped[list["Topping"]] = relationship(
        "Topping", secondary=cart_item_topping, back_populates="cart_items"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
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
    __tablename__ = "cart"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    subtotal: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=Decimal("0.00")
    )
    tax: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=Decimal("0.00")
    )
    delivery_charge: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=Decimal("0.00")
    )
    total: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False, default=Decimal("0.00")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=True)
    user: Mapped["User"] = relationship()
    cart_items: Mapped[list["CartItem"]] = relationship(
        "CartItem", back_populates="cart", cascade="all, delete-orphan"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Cart(id={self.id})>"
