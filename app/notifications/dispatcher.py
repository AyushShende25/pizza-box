import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.utils.logger import logger

from .model import Notification, NotificationPriority, NotificationType
from .pubsub import pubsub_service
from .schema import NotificationCreate
from .service import NotificationService


class NotificationDispatcher:
    @staticmethod
    async def notify_user(
        *,
        user_id: uuid.UUID | str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        payload: dict[str, Any] | None = None,
        expires_in_hours: int | None = None,
        persist: bool = True,
        session: AsyncSession | None = None,
    ):
        """
        Persists a notification (optional) and broadcasts it to the user's active WebSockets via Redis.
        """
        user_uuid = uuid.UUID(str(user_id))
        now = datetime.now(UTC)
        notification: Notification | None = None
        if persist:
            expires_at = (
                now + timedelta(hours=expires_in_hours) if expires_in_hours else None
            )
            create_data = NotificationCreate(
                user_id=user_uuid,
                notification_type=notification_type,
                priority=priority,
                title=title,
                message=message,
                payload=payload,
                expires_at=expires_at,
            )

            if session:
                notification = await NotificationService(session).create_notification(
                    create_data,
                    commit=False,
                )
            else:
                async with AsyncSessionLocal() as db:
                    notification = await NotificationService(db).create_notification(
                        create_data,
                        commit=True,
                    )

        ws_payload = {
            "id": str(notification.id) if notification else None,
            "user_id": str(user_uuid),
            "type": notification_type.value,
            "priority": priority.value,
            "title": title,
            "message": message,
            "payload": payload or {},
            "created_at": (
                notification.created_at.isoformat() if notification else now.isoformat()
            ),
        }

        # Publish to user's dedicated Redis channel
        channel = f"ws:user:{user_uuid}"

        await pubsub_service.publish(channel, ws_payload)

        logger.info(
            f"[Dispatcher] Dispatched user notification to {channel} ({notification_type.value})"
        )

        return notification

    @staticmethod
    async def notify_admins(
        *,
        event_type: str,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        payload: dict[str, Any] | None = None,
    ) -> None:
        """
        Broadcasts an operational alert to all connected admin WebSockets via Redis.
        """
        ws_payload = {
            "scope": "admin",
            "type": event_type,
            "priority": priority.value,
            "title": title,
            "message": message,
            "payload": payload or {},
            "created_at": datetime.now(UTC).isoformat(),
        }

        channel = "ws:admin"

        await pubsub_service.publish(channel, ws_payload)

        logger.info(f"[Dispatcher] Dispatched admin notification ({event_type})")


notification_dispatcher = NotificationDispatcher()
