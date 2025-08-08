import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends
from datetime import timedelta
from app.core.config import settings


class RedisService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    async def store_refresh_token(
        self, jti: str, user_id: str, expires_in: timedelta | None = None
    ):
        """Store refresh token with JTI as key."""
        await self.redis.set(f"refresh:{jti}", user_id, ex=expires_in)

    async def validate_refresh_token(self, jti: str, user_id: str) -> bool:
        """Validate refresh token by comparing stored user_id."""
        stored_id = await self.redis.get(f"refresh:{jti}")
        return stored_id == user_id

    async def revoke_refresh_token(self, jti: str):
        await self.redis.delete(f"refresh:{jti}")

    async def store_verification_token(
        self, token: str, user_id: str, expires_in: timedelta | None = None
    ):
        await self.redis.set(f"verify:{token}", user_id, ex=expires_in)

    async def verify_verification_token(self, token: str):
        user_id = await self.redis.get(f"verify:{token}")
        return user_id

    async def delete_verification_token(self, token: str):
        await self.redis.delete(f"verify:{token}")


redis_client = RedisService()


def get_redis():
    return redis_client


RedisDep = Annotated[RedisService, Depends(get_redis)]
