import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    Enum,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.base import Base

if TYPE_CHECKING:
    from app.auth.model import User


class NotificationType(str, enum.Enum):
    ORDER_UPDATE = "order_update"
    PAYMENT_UPDATE = "payment_update"
    DELIVERY_UPDATE = "delivery_update"
    CART_REMINDER = "cart_reminder"
    PROMOTION = "promotion"
    SYSTEM = "system"


class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        ondelete="CASCADE",
    )
    user: Mapped["User"] = relationship(back_populates="notifications")

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    payload: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
    )

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority),
        default=NotificationPriority.MEDIUM,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    read_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<Notification {self.id} - {self.notification_type} for user {self.user_id}>"
