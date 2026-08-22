from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status

from app.auth.dependencies import (
    CurrentUserDep,
    get_current_admin_ws,
    get_current_user_ws,
)
from app.auth.model import User
from app.notifications.schema import (
    NotificationMarkRead,
    NotificationQueryParams,
    NotificationResponse,
)

from .dependencies import NotificationServiceDep
from .manager import ws_manager

notifications_router = APIRouter(prefix="/notifications", tags=["Notifications"])


@notifications_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[NotificationResponse],
)
async def get_notifications(
    notification_service: NotificationServiceDep,
    current_user: CurrentUserDep,
    notification_params: Annotated[NotificationQueryParams, Query()],
):
    return await notification_service.get_user_notifications(
        user_id=current_user.id,
        limit=notification_params.limit,
        status=notification_params.status,
        before=notification_params.before,
    )


@notifications_router.post(
    "/mark-read",
    status_code=status.HTTP_200_OK,
)
async def mark_read(
    notification_service: NotificationServiceDep,
    current_user: CurrentUserDep,
    payload: NotificationMarkRead,
):
    await notification_service.mark_many_as_read(
        ids=payload.notification_ids,
        user_id=current_user.id,
    )
    return {
        "status": "success",
        "message": "Notifications marked as read",
    }


@notifications_router.get(
    "/unread-count",
    status_code=status.HTTP_200_OK,
)
async def get_unread_count(
    notification_service: NotificationServiceDep,
    current_user: CurrentUserDep,
):
    count = await notification_service.get_unread_count(current_user.id)

    return {"count": count}


@notifications_router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_notification(
    notification_id: UUID,
    notification_service: NotificationServiceDep,
    current_user: CurrentUserDep,
):
    await notification_service.delete_notification(
        id=notification_id,
        user_id=current_user.id,
    )
    return {
        "status": "success",
        "message": "Notification deleted",
    }


@notifications_router.websocket("/ws")
async def user_notification_ws(
    websocket: WebSocket,
    current_user: Annotated[User, Depends(get_current_user_ws)],
):
    await ws_manager.connect_user(user_id=current_user.id, websocket=websocket)

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        await ws_manager.disconnect_user(user_id=current_user.id, websocket=websocket)
    except Exception:
        await ws_manager.disconnect_user(user_id=current_user.id, websocket=websocket)


@notifications_router.websocket("/ws/admin")
async def admin_notifications_ws(
    websocket: WebSocket,
    current_user: Annotated[User, Depends(get_current_admin_ws)],
):
    await ws_manager.connect_admin(websocket=websocket)

    try:
        while True:
            await websocket.receive_json()
    except WebSocketDisconnect:
        await ws_manager.disconnect_admin(websocket=websocket)
    except Exception:
        await ws_manager.disconnect_admin(websocket=websocket)
