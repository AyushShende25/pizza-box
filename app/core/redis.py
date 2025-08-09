import redis.asyncio as redis
from typing import Annotated
from fastapi import Depends
from datetime import timedelta
from app.core.config import settings


class RedisService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_refresh_token_key(self, jti: str):
        return f"refresh:{jti}"

    def get_verification_token_key(self, token: str):
        return f"verify:{token}"

    async def store_refresh_token(
        self, jti: str, user_id: str, expires_in: timedelta | None = None
    ):
        """Store refresh token with JTI as key."""
        key = self.get_refresh_token_key(jti)
        await self.redis.set(key, user_id, ex=expires_in)

    async def validate_refresh_token(self, jti: str, user_id: str) -> bool:
        """Validate refresh token by comparing stored user_id."""
        key = self.get_refresh_token_key(jti)
        stored_id = await self.redis.get(key)
        return stored_id == user_id

    async def revoke_refresh_token(self, jti: str):
        key = self.get_refresh_token_key(jti)
        await self.redis.delete(key)

    async def store_verification_token(
        self, token: str, user_id: str, expires_in: timedelta | None = None
    ):
        key = self.get_verification_token_key(token)
        await self.redis.set(key, user_id, ex=expires_in)

    async def verify_verification_token(self, token: str):
        key = self.get_verification_token_key(token)
        user_id = await self.redis.get(key)
        if not user_id:
            return None
        return user_id

    async def delete_verification_token(self, token: str):
        key = self.get_verification_token_key(token)
        await self.redis.delete(key)


redis_client = RedisService()


def get_redis():
    return redis_client


RedisDep = Annotated[RedisService, Depends(get_redis)]
