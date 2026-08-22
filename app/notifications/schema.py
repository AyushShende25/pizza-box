import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import Field

from app.core.base_schema import BaseSchema
from app.notifications.model import (
    NotificationPriority,
    NotificationType,
)


class NotificationCreate(BaseSchema):
    user_id: uuid.UUID
    notification_type: NotificationType
    priority: NotificationPriority = NotificationPriority.MEDIUM
    title: str = Field(min_length=1, max_length=255)
    message: str = Field(min_length=1, max_length=500)
    payload: dict[str, Any] | None = None
    expires_at: datetime | None = None


class NotificationResponse(BaseSchema):
    id: uuid.UUID
    user_id: uuid.UUID
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    payload: dict[str, Any] | None
    is_read: bool
    read_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class NotificationMarkRead(BaseSchema):
    notification_ids: list[uuid.UUID]


NotificationStatus = Literal["read", "unread"]


class NotificationQueryParams(BaseSchema):
    limit: int = Field(default=10, ge=1, le=100)
    status: NotificationStatus | None = None
    before: datetime | None = None
