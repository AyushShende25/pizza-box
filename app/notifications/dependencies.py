from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep

from .service import NotificationService


def get_notification_service(session: SessionDep) -> NotificationService:
    """Provides a fresh NotificationService instance"""
    return NotificationService(session)


NotificationServiceDep = Annotated[
    NotificationService, Depends(get_notification_service)
]
