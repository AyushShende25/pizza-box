import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    DECIMAL,
    TIMESTAMP,
    Boolean,
    Column,
    Enum,
    ForeignKey,
    String,
    Table,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.cart.model import CartItem, cart_item_topping
from app.core.base import Base


class FoodType(str, enum.Enum):
    VEG = "veg"
    NON_VEG = "non_veg"


class ToppingCategory(str, enum.Enum):
    MEAT = "meat"
    VEGETABLE = "vegetable"
    CHEESE = "cheese"
    SAUCE = "sauce"


pizza_toppings = Table(
    "pizza_toppings",
    Base.metadata,
    Column(
        "pizza_id",
        Uuid(as_uuid=True),
        ForeignKey("pizzas.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topping_id",
        Uuid(as_uuid=True),
        ForeignKey("toppings.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Pizza(Base):
    __tablename__ = "pizzas"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        unique=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    base_price: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        comment="Base price for regular size",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    food_type: Mapped[FoodType] = mapped_column(
        Enum(FoodType, name="food_type_enum"),
        nullable=False,
        index=True,
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    # Default toppings included in base price
    default_toppings: Mapped[list["Topping"]] = relationship(
        secondary=pizza_toppings,
        back_populates="pizzas",
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
        return f"<Pizza(id={self.id}, name={self.name}, food_type={self.food_type})>"


class Size(Base):
    __tablename__ = "sizes"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    price_modifier: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Size(name={self.name}, price_modifier={self.price_modifier})>"


class Crust(Base):
    __tablename__ = "crusts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    price_modifier: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        default=Decimal("0.00"),
        nullable=False,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Crust(name={self.name}, price_modifier={self.price_modifier})>"


class Topping(Base):
    __tablename__ = "toppings"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    price_modifier: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    category: Mapped[ToppingCategory] = mapped_column(
        Enum(ToppingCategory, name="topping_category_enum"),
        nullable=False,
    )
    food_type: Mapped[FoodType] = mapped_column(
        Enum(FoodType, name="food_type_enum"),
        nullable=False,
        index=True,
    )
    is_available: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    sort_order: Mapped[int] = mapped_column(
        nullable=False,
        default=0,
    )

    pizzas: Mapped[list["Pizza"]] = relationship(
        secondary=pizza_toppings,
        back_populates="default_toppings",
    )

    cart_items: Mapped[list["CartItem"]] = relationship(
        secondary=cart_item_topping,
        back_populates="toppings",
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Topping(name={self.name}, price_modifier={self.price_modifier}, category={self.category})>"
