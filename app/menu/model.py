from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (
    String,
    Uuid,
    TIMESTAMP,
    func,
    Boolean,
    ForeignKey,
    Float,
    Table,
    Column,
    Enum,
    Text,
)
from datetime import datetime
import uuid
import enum
from app.core.base import Base


class PizzaCategory(enum.Enum):
    VEG = "veg"
    NON_VEG = "non_veg"


class ToppingCategory(enum.Enum):
    MEAT = "meat"
    VEGETABLE = "vegetable"
    CHEESE = "cheese"
    SAUCE = "sauce"
    SPICE = "spice"


pizza_toppings = Table(
    "pizza_toppings",
    Base.metadata,
    Column(
        "pizza_id",
        Uuid(as_uuid=True),
        ForeignKey("pizza.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "topping_id",
        Uuid(as_uuid=True),
        ForeignKey("topping.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Pizza(Base):
    __tablename__ = "pizza"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    base_price: Mapped[float] = mapped_column(
        Float, nullable=False, comment="Base price for regular size"
    )
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    category: Mapped[PizzaCategory] = mapped_column(Enum(PizzaCategory), nullable=False)

    # Default toppings included in base price
    default_toppings: Mapped[list["Topping"]] = relationship(
        "Topping", secondary=pizza_toppings, back_populates="pizzas", lazy="selectin"
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
        return f"<Pizza(id={self.id}, name={self.name}, category={self.category})>"


class Size(Base):
    __tablename__ = "size"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    multiplier: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<Size(name={self.name}, multiplier={self.multiplier})>"


class Crust(Base):
    __tablename__ = "crust"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    additional_price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<Crust(name={self.name}, additional_price={self.additional_price})>"


class Topping(Base):
    __tablename__ = "topping"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    category: Mapped[ToppingCategory] = mapped_column(
        Enum(ToppingCategory), nullable=False
    )
    is_vegetarian: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    pizzas: Mapped[list["Pizza"]] = relationship(
        "Pizza", secondary=pizza_toppings, back_populates="default_toppings"
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return (
            f"<Topping(name={self.name}, price={self.price}, category={self.category})>"
        )
