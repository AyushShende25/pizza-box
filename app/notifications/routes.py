from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from app.core.database import get_session, SessionDep
from app.auth.dependencies import (
    get_current_user_ws,
    UserOrAdminDep,
    get_current_admin_ws,
)
from app.auth.model import User
from app.notifications.manager import notifications_manager
from app.notifications.service import NotificationService
from app.notifications.schema import (
    NotificationMarkRead,
    NotificationRead,
    NotificationQueryParams,
)
from uuid import UUID

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get("/", response_model=list[NotificationRead])
async def get_notifications(
    session: SessionDep,
    current_user: UserOrAdminDep,
    notification_params: Annotated[NotificationQueryParams, Query()],
):
    return await NotificationService(session=session).get_user_notifications(
        user_id=current_user.id,
        limit=notification_params.limit,
        status=notification_params.status,
    )


@notifications_router.post("/mark-read")
async def mark_read(
    session: SessionDep, current_user: UserOrAdminDep, payload: NotificationMarkRead
):
    await NotificationService(session=session).mark_many_as_read(
        ids=payload.notification_ids,
        user_id=current_user.id,
    )
    return {"status": "success", "message": "Notifications marked as read"}


@notifications_router.delete("/{notification_id}")
async def delete_notification(
    notification_id: UUID,
    session: SessionDep,
    current_user: UserOrAdminDep,
):
    await NotificationService(session=session).delete_notification(
        id=notification_id,
        user_id=current_user.id,
    )
    return {"status": "success", "message": "Notification deleted"}


@notifications_router.websocket("/ws")
async def notifications_ws(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user_ws)],
):
    user_id = str(current_user.id)
    await notifications_manager.connect_user(user_id=user_id, websocket=websocket)

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        await notifications_manager.disconnect_user(
            user_id=user_id, websocket=websocket
        )
    except Exception:
        await notifications_manager.disconnect_user(
            user_id=user_id, websocket=websocket
        )


@notifications_router.websocket("/ws/admin")
async def admin_notifications_ws(
    websocket: WebSocket,
    db: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_admin_ws)],
):
    await notifications_manager.connect_admin(websocket=websocket)

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        await notifications_manager.disconnect_admin(websocket=websocket)
    except Exception:
        await notifications_manager.disconnect_admin(websocket=websocket)
