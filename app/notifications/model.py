from app.core.base import Base
from sqlalchemy import (
    Uuid,
    TIMESTAMP,
    func,
    ForeignKey,
    String,
    JSON,
    Enum,
    Boolean,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from datetime import datetime
import enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.auth.model import User


class NotificationType(enum.Enum):
    ORDER_UPDATE = "order_update"
    PAYMENT_UPDATE = "payment_update"
    DELIVERY_UPDATE = "delivery_update"
    CART_REMINDER = "cart_reminder"
    PROMOTION = "promotion"
    SYSTEM = "system"


class NotificationChannel(enum.Enum):
    WEBSOCKET = "websocket"
    EMAIL = "email"


class NotificationPriority(enum.Enum):
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
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    data: Mapped[dict] = mapped_column(JSON, nullable=True)

    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType),
        nullable=False,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority),
        default=NotificationPriority.MEDIUM,
        nullable=False,
    )
    channels: Mapped[list[NotificationChannel]] = mapped_column(
        ARRAY(Enum(NotificationChannel)),
        default=list,
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    read_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
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

    user: Mapped["User"] = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification {self.id} - {self.notification_type} for user {self.user_id}>"
