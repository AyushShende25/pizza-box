import json
from typing import Any

import redis.asyncio as redis

from app.core.config import settings
from app.utils.logger import logger


class PubSubService:
    def __init__(self):
        self._client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )

    def get_pubsub(self):
        """Creates a dedicated PubSub instance for a background consumer."""
        return self._client.pubsub()

    async def publish(
        self,
        channel: str,
        event_data: dict[str, Any],
    ):
        """Publishes a JSON payload to a Redis channel."""
        try:
            subscribers_count = await self._client.publish(
                channel,
                json.dumps(event_data),
            )

            logger.info(
                f"Published to {channel}: {event_data.get('event_type')} - {subscribers_count} subscribers"
            )

            return subscribers_count

        except Exception as e:
            logger.exception(f"Error publishing to channel:{channel}: {e}")
            raise

    async def close(self):
        await self._client.close()


pubsub_service = PubSubService()
