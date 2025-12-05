from typing import List, Dict
from fastapi import WebSocket
from app.utils.logger import logger


class NotificationsManager:
    def __init__(self):
        self.active_user_connections: Dict[str, List[WebSocket]] = {}
        self.active_admin_connections: List[WebSocket] = []

    async def connect_user(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_user_connections.setdefault(user_id, []).append(websocket)
        logger.info(
            f"WS connected: user={user_id}, "
            f"total={len(self.active_user_connections[user_id])}"
        )

    async def connect_admin(self, websocket: WebSocket):
        await websocket.accept()
        self.active_admin_connections.append(websocket)
        logger.info(f"WS connected: ADMIN, total={len(self.active_admin_connections)}")

    async def send_to_user(self, user_id: str, message: dict):
        connections = self.active_user_connections.get(user_id, [])
        await self._safe_send(connections, message)

    async def send_to_admin(self, message: dict):
        await self._safe_send(self.active_admin_connections, message)

    async def _safe_send(self, connections: List[WebSocket], message: dict):
        disconnected = []
        for ws in connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            connections.remove(ws)

    async def disconnect_user(self, user_id: str, websocket: WebSocket):
        connections = self.active_user_connections.get(user_id)
        if not connections:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            del self.active_user_connections[user_id]

        logger.info(f"WS disconnected: user={user_id}")

    async def disconnect_admin(self, websocket: WebSocket):
        if websocket in self.active_admin_connections:
            self.active_admin_connections.remove(websocket)

        logger.info("WS disconnected: ADMIN")

    async def broadcast_to_all_users(self, message: dict):
        all_connections = []
        for connections in self.active_user_connections.values():
            all_connections.extend(connections)

        await self._safe_send(all_connections, message)


notifications_manager = NotificationsManager()
