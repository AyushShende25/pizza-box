from app.core.base_schema import BaseSchema
import uuid
from app.notifications.model import (
    NotificationType,
    NotificationPriority,
    NotificationChannel,
)
from pydantic import Field
from typing import Dict, Any, List, Literal
from decimal import Decimal
from datetime import datetime
from app.orders.model import OrderStatus, PaymentStatus
from app.payments.model import PaymentTransactionStatus, PaymentProvider


class NotificationBase(BaseSchema):
    user_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=500)
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    data: Dict[str, Any] | None = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID
    channels: List[NotificationChannel] | None = [NotificationChannel.WEBSOCKET]
    expires_in_hours: int | None = None


class NotificationRead(NotificationBase):
    id: uuid.UUID
    channels: List[NotificationChannel]
    is_read: bool
    read_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    updated_at: datetime


class OrderEventData(BaseSchema):
    order_id: uuid.UUID
    order_num: str
    user_id: uuid.UUID
    status: OrderStatus
    status_message: str | None = None
    payment_status: PaymentStatus | None = None
    total_amount: Decimal | None = None
    reason: str | None = None
    delay_minutes: int | None = None


class PaymentEventData(BaseSchema):
    user_id: uuid.UUID
    order_num: str
    payment_status: PaymentTransactionStatus
    provider: PaymentProvider
    amount: Decimal | None = None
    reason: str | None = None


class NotificationMarkRead(BaseSchema):
    notification_ids: list[uuid.UUID]


class NotificationQueryParams(BaseSchema):
    limit: int = Field(default=10, ge=1, le=100)
    status: Literal["read", "unread"] | None = None
