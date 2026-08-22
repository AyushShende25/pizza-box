from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.notifications.model import Notification
from app.notifications.schema import NotificationCreate, NotificationStatus


class NotificationService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def create_notification(
        self,
        data: NotificationCreate,
        commit: bool = True,
    ) -> Notification:
        notification = Notification(**data.model_dump())

        self.session.add(notification)

        if commit:
            await self.session.commit()
            await self.session.refresh(notification)
        else:
            await self.session.flush()

        return notification

    async def get_user_notifications(
        self,
        user_id: UUID,
        limit: int,
        status: NotificationStatus | None = None,
        before: datetime | None = None,
    ) -> list[Notification]:
        now = datetime.now(UTC)
        query = select(Notification).where(
            Notification.user_id == user_id,
            or_(Notification.expires_at.is_(None), Notification.expires_at > now),
        )

        if status == "read":
            query = query.where(Notification.is_read.is_(True))
        elif status == "unread":
            query = query.where(Notification.is_read.is_(False))

        if before is not None:
            query = query.where(Notification.created_at < before)

        query = query.order_by(Notification.created_at.desc()).limit(limit)

        result = await self.session.execute(query)

        return list(result.scalars().all())

    async def get_unread_count(self, user_id: UUID) -> int:
        now = datetime.now(UTC)

        query = (
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                or_(Notification.expires_at.is_(None), Notification.expires_at > now),
            )
        )

        result = await self.session.execute(query)

        return result.scalar() or 0

    async def mark_many_as_read(
        self,
        ids: list[UUID],
        user_id: UUID,
    ) -> int:
        if not ids:
            return 0

        stmt = (
            update(Notification)
            .where(
                Notification.id.in_(ids),
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True, read_at=datetime.now(UTC))
        )

        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount

    async def delete_notification(
        self,
        id: UUID,
        user_id: UUID,
    ) -> bool:
        stmt = delete(Notification).where(
            Notification.id == id,
            Notification.user_id == user_id,
        )

        result = await self.session.execute(stmt)

        await self.session.commit()
        return result.rowcount > 0
