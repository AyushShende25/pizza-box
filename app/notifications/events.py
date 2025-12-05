from datetime import datetime, timezone
import asyncio
from typing import Dict, Any
from app.notifications.redis_pubsub import pubsub_service
from app.utils.logger import logger
from app.notifications.model import NotificationPriority
from app.notifications.service import NotificationService
from app.core.database import async_session
from app.notifications.manager import notifications_manager
from app.notifications.schema import (
    NotificationCreate,
    OrderEventData,
    PaymentEventData,
)
from app.notifications.model import NotificationType, NotificationChannel
import uuid


class Channels:
    ORDER_EVENTS = "order_events"
    PAYMENT_EVENTS = "payment_events"
    DELIVERY_EVENTS = "delivery_events"
    CART_EVENTS = "cart_events"
    PROMO_EVENTS = "promo_events"


async def start_event_listener():
    try:
        channels = [
            Channels.ORDER_EVENTS,
            Channels.PAYMENT_EVENTS,
            Channels.DELIVERY_EVENTS,
            Channels.CART_EVENTS,
            Channels.PROMO_EVENTS,
        ]
        await pubsub_service.subscribe(*channels)
        logger.info("Event listener started.")

        async for message in pubsub_service.listen():
            channel = message["channel"]
            data = message["data"]
            try:
                await route_event(channel=channel, event_data=data)
            except Exception as e:
                logger.error(f"Error handling event from {channel}: {e}", exc_info=True)
    except asyncio.CancelledError:
        logger.info("Event listener cancelled")
        await pubsub_service.close()
    except Exception as e:
        logger.error(f"Event listener error: {e}", exc_info=True)
        await pubsub_service.close()


async def route_event(channel: str, event_data: Dict[str, Any]):
    match channel:
        case Channels.ORDER_EVENTS:
            await handle_order_event(event_data)
        case Channels.PAYMENT_EVENTS:
            await handle_payment_event(event_data)
        case _:
            logger.warning(f"Unknown event channel: {channel}")


async def handle_order_event(event_data: Dict[str, Any]):
    event_type = event_data.get("event_type")
    user_id = event_data.get("user_id")
    if not event_type or not user_id:
        logger.warning(f"Missing required fields in order event: {event_data}")
        return

    template = ORDER_EVENT_TEMPLATES.get(event_type)
    if not template:
        logger.warning(f"Unhandled order event: {event_data}")
        return

    await dispatch_notification_from_template(
        user_id=user_id,
        event_data=event_data,
        template=template,
    )


async def handle_payment_event(event_data: Dict[str, Any]):
    event_type = event_data.get("event_type")
    user_id = event_data.get("user_id")
    if not event_type or not user_id:
        logger.warning(f"Missing required fields in order event: {event_data}")
        return

    template = PAYMENT_EVENT_TEMPLATES.get(event_type)
    if not template:
        logger.warning(f"Unhandled payment event: {event_data}")
        return

    await dispatch_notification_from_template(
        user_id=user_id,
        event_data=event_data,
        template=template,
    )


async def dispatch_notification_from_template(
    *,
    user_id: uuid.UUID | None,
    event_data: dict,
    template: dict,
):
    if user_id and "user" in template:
        user_tpl = template["user"]
        if user_tpl.get("persist", True):
            async with async_session() as session:
                notification = await NotificationService(session).create_notification(
                    data=NotificationCreate(
                        user_id=user_id,
                        notification_type=user_tpl["type"],
                        title=user_tpl["title"],
                        message=user_tpl["message"].format(**event_data),
                        priority=user_tpl["priority"],
                        data=event_data,
                        channels=user_tpl["channels"],
                        expires_in_hours=user_tpl["expires_in_hours"],
                    )
                )

            await notifications_manager.send_to_user(
                user_id=user_id,
                message={
                    "id": str(notification.id) if notification else None,
                    "type": user_tpl["type"].value,
                    "title": user_tpl["title"],
                    "message": user_tpl["message"].format(**event_data),
                    "priority": user_tpl["priority"].value,
                    "data": event_data,
                    "created_at": (
                        notification.created_at.isoformat()
                        if notification
                        else datetime.now(timezone.utc).isoformat()
                    ),
                },
            )
    if "admin" in template:
        admin_tpl = template["admin"]

        admin_payload = {
            "scope": "admin",
            "type": admin_tpl["ws_type"],
            "title": admin_tpl["title"],
            "message": admin_tpl["message"].format(**event_data),
            "priority": admin_tpl["priority"].value,
            "data": event_data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        await notifications_manager.send_to_admin(admin_payload)


async def publish_order_event(event_type: str, data: OrderEventData):
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data.model_dump(exclude_unset=True, mode="json"),
    }
    await pubsub_service.publish(Channels.ORDER_EVENTS, event_data=event)


async def publish_payment_event(event_type: str, data: PaymentEventData):
    event = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **data.model_dump(exclude_unset=True, mode="json"),
    }
    await pubsub_service.publish(Channels.PAYMENT_EVENTS, event_data=event)


ORDER_EVENT_TEMPLATES = {
    "order_created": {
        "user": {
            "title": "Order Placed!",
            "message": "Your order #{order_num} has been placed.",
            "priority": NotificationPriority.HIGH,
            "type": NotificationType.ORDER_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 48,
            "persist": True,
        },
        "admin": {
            "title": "New Order",
            "message": "Order #{order_num} placed by user {user_id}",
            "priority": NotificationPriority.HIGH,
            "ws_type": "ORDER_CREATED",
            "persist": False,
        },
    },
    "order_status_changed": {
        "user": {
            "title": "Order Status Update",
            "message": "{status_message}",
            "priority": NotificationPriority.MEDIUM,
            "type": NotificationType.ORDER_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 48,
            "persist": True,
        },
        "admin": {
            "title": "Order Status Changed",
            "message": "Order #{order_num} → {status}",
            "priority": NotificationPriority.MEDIUM,
            "ws_type": "ORDER_STATUS_CHANGED",
            "persist": False,
        },
    },
    "order_delayed": {
        "user": {
            "title": "Order Delayed",
            "message": "Your order is delayed by {delay_minutes} minutes.",
            "priority": NotificationPriority.MEDIUM,
            "type": NotificationType.ORDER_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 24,
            "persist": True,
        },
        "admin": {
            "title": "Order Delayed",
            "message": "Order #{order_num} delayed by {delay_minutes} min",
            "priority": NotificationPriority.HIGH,
            "ws_type": "ORDER_DELAYED",
            "persist": False,
        },
    },
    "order_cancelled": {
        "user": {
            "title": "Order Cancelled",
            "message": "Your order #{order_num} has been cancelled. {reason}",
            "priority": NotificationPriority.MEDIUM,
            "type": NotificationType.ORDER_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 48,
            "persist": True,
        },
        "admin": {
            "title": "Order Cancelled",
            "message": "Order #{order_num} cancelled. Reason: {reason}",
            "priority": NotificationPriority.MEDIUM,
            "ws_type": "ORDER_CANCELLED",
            "persist": False,
        },
    },
}

PAYMENT_EVENT_TEMPLATES = {
    "payment_successful": {
        "user": {
            "title": "Payment Successful",
            "message": "Payment of ₹{amount} received for order #{order_num}",
            "priority": NotificationPriority.HIGH,
            "type": NotificationType.PAYMENT_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 48,
            "persist": True,
        },
        "admin": {
            "title": "Payment Successful",
            "message": "₹{amount} received for order #{order_num}",
            "priority": NotificationPriority.MEDIUM,
            "ws_type": "PAYMENT_SUCCESSFUL",
            "persist": False,
        },
    },
    "payment_failed": {
        "user": {
            "title": "Payment Failed",
            "message": "Payment failed: {reason}. Please try again.",
            "priority": NotificationPriority.HIGH,
            "type": NotificationType.PAYMENT_UPDATE,
            "channels": [NotificationChannel.WEBSOCKET],
            "expires_in_hours": 48,
            "persist": True,
        },
        "admin": {
            "title": "Payment Failed",
            "message": "Order #{order_num} payment failed",
            "priority": NotificationPriority.HIGH,
            "ws_type": "PAYMENT_FAILED",
            "persist": False,
        },
    },
}
