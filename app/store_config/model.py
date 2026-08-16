from datetime import datetime
from decimal import Decimal

from sqlalchemy import DECIMAL, TIMESTAMP, Boolean, CheckConstraint, Float, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base import Base


class StoreConfig(Base):
    __tablename__ = "store_config"

    __table_args__ = (
        CheckConstraint(
            "max_delivery_km >= 0",
            name="ck_max_delivery_km_fee_positive",
        ),
        CheckConstraint(
            "min_order_value >= 0",
            name="ck_min_order_positive",
        ),
        CheckConstraint(
            "base_delivery_fee >= 0",
            name="ck_delivery_fee_positive",
        ),
        CheckConstraint(
            "per_km_fee >= 0",
            name="ck_per_km_fee_positive",
        ),
        CheckConstraint(
            "latitude >= -90 AND latitude <= 90",
            name="ck_latitude_range",
        ),
        CheckConstraint(
            "longitude >= -180 AND longitude <= 180",
            name="ck_longitude_range",
        ),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        default=1,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Pizza Box",
    )
    phone_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    address: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    max_delivery_km: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=20.0,
    )
    is_accepting_orders: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    min_order_value: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("0.00"),
    )
    base_delivery_fee: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("30.00"),
    )
    per_km_fee: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
        default=Decimal("5.00"),
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
