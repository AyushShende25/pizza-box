import json
import redis.asyncio as redis
from typing import Dict, Any, AsyncGenerator
from app.core.config import settings
from app.utils.logger import logger


class RedisPubSubService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            encoding="utf-8",
        )
        self.pubsub = None

    async def publish(self, channel: str, event_data: Dict[str, Any]) -> int:
        try:
            message = json.dumps(event_data)
            subscribers = await self.redis_client.publish(channel, message)
            logger.info(
                f"Published to {channel}: {event_data.get('event_type')} - {subscribers} subscribers"
            )
            return subscribers
        except Exception as e:
            logger.error(f"Error publishing to {channel}: {e}", exc_info=True)
            raise

    async def subscribe(
        self,
        *channels: str,
    ) -> None:
        if not self.pubsub:
            self.pubsub = self.redis_client.pubsub()
        await self.pubsub.subscribe(*channels)
        logger.info(f"Subscribed to channels {channels}")

    async def unsubscribe(
        self,
        channel: str,
    ) -> None:
        if self.pubsub:
            await self.pubsub.unsubscribe(channel)
            logger.info(f"Unsubscribed from channel {channel}")

    async def listen(self) -> AsyncGenerator[Dict[str, Any], None]:
        if not self.pubsub:
            raise RuntimeError("PubSub is not initialized. Call subscribe() first.")

        async for message in self.pubsub.listen():
            if message.get("type") == "message":
                try:
                    channel = message["channel"]
                    data = json.loads(message["data"])
                    yield {"channel": channel, "data": data}
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    continue

    async def close(self) -> None:
        if self.pubsub:
            await self.pubsub.close()
        await self.redis_client.close()
        logger.info("Closed Redis Pub/Sub connection")


pubsub_service = RedisPubSubService()
