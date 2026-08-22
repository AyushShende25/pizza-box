from uuid import UUID

from fastapi import WebSocket

from app.utils.logger import logger


class WSManager:
    def __init__(self):
        # Maps user_id -> set of active WebSockets
        self._user_connections: dict[str, set[WebSocket]] = {}
        self._admin_connections: set[WebSocket] = set()

    async def connect_user(
        self,
        user_id: UUID | str,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        key = str(user_id)

        if key not in self._user_connections:
            self._user_connections[key] = set()
        self._user_connections[key].add(websocket)

        logger.info(
            f"[WS] Connected user={key} (Total: {len(self._user_connections[key])})"
        )

    async def disconnect_user(
        self,
        user_id: UUID | str,
        websocket: WebSocket,
    ) -> None:
        key = str(user_id)

        if key in self._user_connections:
            self._user_connections[key].discard(websocket)

            # If empty then remove the map
            if not self._user_connections[key]:
                del self._user_connections[key]

        logger.info(f"[WS] Disconnected user={key}")

    async def connect_admin(self, websocket: WebSocket) -> None:
        await websocket.accept()

        self._admin_connections.add(websocket)

        logger.info(f"[WS] Connected admin (Total: {len(self._admin_connections)})")

    async def disconnect_admin(self, websocket: WebSocket) -> None:
        self._admin_connections.discard(websocket)

        logger.info(f"[WS] Disconnected admin (Total: {len(self._admin_connections)})")

    async def send_to_user(self, user_id: UUID | str, message: dict) -> None:
        key = str(user_id)

        sockets = self._user_connections.get(key)

        if not sockets:
            return

        await self._safe_broadcast(sockets, message)

    async def send_to_admin(self, message: dict) -> None:
        if not self._admin_connections:
            return

        await self._safe_broadcast(self._admin_connections, message)

    async def _safe_broadcast(self, sockets: set[WebSocket], message: dict) -> None:
        dead_sockets = []
        for ws in list(sockets):
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)

        for ws in dead_sockets:
            sockets.discard(ws)
            try:
                await ws.close()
            except Exception:
                pass


ws_manager = WSManager()
