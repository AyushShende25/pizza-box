import enum
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DECIMAL, JSON, TIMESTAMP, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.auth.model import User
    from app.orders.model import Order


class PaymentProvider(str, enum.Enum):
    RAZORPAY = "razorpay"


class PaymentTransactionStatus(str, enum.Enum):
    INITIATED = "initiated"  # Payment created in Razorpay
    PENDING = "pending"  # Awaiting user action
    SUCCESS = "success"  # Payment successful
    FAILED = "failed"  # Payment failed
    REFUNDED = "refunded"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    order_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    order: Mapped["Order"] = relationship(back_populates="payments")

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    user: Mapped["User"] = relationship()

    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider),
        default=PaymentProvider.RAZORPAY,
        nullable=False,
    )
    status: Mapped[PaymentTransactionStatus] = mapped_column(
        Enum(PaymentTransactionStatus),
        default=PaymentTransactionStatus.INITIATED,
        nullable=False,
    )

    razorpay_order_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    razorpay_payment_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    razorpay_signature: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2),
        nullable=False,
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="INR",
    )

    meta_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    initiated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
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
