import asyncio
import json
from typing import Any

from app.utils.logger import logger

from .manager import WSManager, ws_manager
from .pubsub import PubSubService, pubsub_service


class NotificationListener:
    SUBSCRIBE_PATTERN = "ws:*"

    def __init__(self, pubsub: PubSubService, ws: WSManager):
        self._pubsub = pubsub
        self._ws = ws
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            logger.warning("[WS Listener] Already running")
            return

        self._running = True

        self._task = asyncio.create_task(self._run_loop(), name="notification-listener")

        logger.info(f"[WS Listener] Started listening to {self.SUBSCRIBE_PATTERN}")

    async def stop(self) -> None:
        self._running = False

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[WS Listener] Stopped")

    async def _run_loop(self) -> None:
        while self._running:
            pubsub_instance = self._pubsub.get_pubsub()
            try:
                await pubsub_instance.psubscribe(self.SUBSCRIBE_PATTERN)
                async for raw_message in pubsub_instance.listen():
                    if raw_message["type"] != "pmessage":
                        continue

                    await self._dispatch(
                        channel=raw_message["channel"],
                        raw_data=raw_message["data"],
                    )
            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error(
                    f"[WS Listener] Connection dropped: {exc}. Retrying in 5s...",
                    exc_info=True,
                )
                await asyncio.sleep(5)
            finally:
                try:
                    await pubsub_instance.punsubscribe(self.SUBSCRIBE_PATTERN)
                    await pubsub_instance.aclose()
                except Exception:
                    pass

    async def _dispatch(self, channel: str, raw_data: Any) -> None:
        try:
            payload: dict = (
                json.loads(raw_data) if isinstance(raw_data, str) else raw_data
            )
        except (json.JSONDecodeError, TypeError) as exc:
            logger.error(f"[WS Listener] Invalid payload on {channel}: {exc}")
            return

        if channel == "ws:admin":
            await self._ws.send_to_admin(payload)
            return

        parts = channel.split(":")
        if len(parts) == 3 and parts[1] == "user":
            user_id = parts[2]
            await self._ws.send_to_user(user_id=user_id, message=payload)


notification_listener = NotificationListener(
    pubsub=pubsub_service,
    ws=ws_manager,
)
