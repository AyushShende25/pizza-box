from sqlalchemy.ext.asyncio import AsyncSession
from app.notifications.schema import NotificationCreate
from app.notifications.model import Notification
from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select, update, delete


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_notification(self, data: NotificationCreate):
        expires_at = None

        if data.expires_in_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(
                hours=data.expires_in_hours
            )
        notification = Notification(
            **data.model_dump(exclude={"expires_in_hours"}),
            expires_at=expires_at,
        )
        self.session.add(notification)
        await self.session.commit()
        await self.session.refresh(notification)
        return notification

    async def get_user_notifications(
        self, user_id: UUID, limit: int, status: str | None
    ):
        query = select(Notification).where(Notification.user_id == user_id)
        if status is not None:
            query = query.where(Notification.is_read == (status == "read"))

        query = query.order_by(Notification.created_at.desc()).limit(limit)

        notifications = await self.session.scalars(query)
        return notifications.all()

    async def mark_many_as_read(self, ids: list[UUID], user_id: UUID):
        stmt = (
            update(Notification)
            .where(Notification.id.in_(ids), Notification.user_id == user_id)
            .values(is_read=True, read_at=datetime.utcnow())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def delete_notification(self, id: UUID, user_id: UUID):
        stmt = delete(Notification).where(
            Notification.id == id,
            Notification.user_id == user_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
