import redis.asyncio as redis
from typing import Annotated, Literal
from fastapi import Depends
from datetime import timedelta
from app.core.config import settings

TokenType = Literal["reset", "verification"]


class RedisService:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL, decode_responses=True)

    def get_refresh_jti_key(self, jti: str):
        return f"refresh:{jti}"

    def get_user_refresh_jtis_key(self, user_id: str):
        return f"user_refresh:{user_id}"

    async def store_refresh_jti(
        self,
        jti: str,
        user_id: str,
        expires_in: timedelta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ):
        """Store refresh-token-id."""
        key = self.get_refresh_jti_key(jti)
        await self.redis.set(key, user_id, ex=expires_in)

        # Add JTI to user's active tokens set
        user_jtis_key = self.get_user_refresh_jtis_key(user_id)
        await self.redis.sadd(user_jtis_key, jti)
        await self.redis.expire(user_jtis_key, expires_in)

    async def validate_refresh_jti(self, jti: str, user_id: str) -> bool:
        """Validate refresh-token-id by comparing stored user_id."""
        key = self.get_refresh_jti_key(jti)
        stored_user_id = await self.redis.get(key)
        return stored_user_id == user_id

    async def revoke_refresh_jti(self, jti: str):
        """Revoke a single refresh token-id."""
        key = self.get_refresh_jti_key(jti)
        user_id = await self.redis.get(key)
        if user_id:
            # Remove jti from user's token set
            user_jtis_key = self.get_user_refresh_jtis_key(user_id)
            await self.redis.srem(user_jtis_key, jti)
        await self.redis.delete(key)

    async def revoke_all_user_refresh_jtis(self, user_id: str):
        """Revoke all refresh token ids for a specific user."""
        user_jtis_key = self.get_user_refresh_jtis_key(user_id)

        # Get all JTIs for this user
        jtis = await self.redis.smembers(user_jtis_key)

        if jtis:
            # Delete all refresh token ids
            token_id_keys = [self.get_refresh_jti_key(jti) for jti in jtis]
            await self.redis.delete(*token_id_keys)

            # Clear the user's token set
            await self.redis.delete(user_jtis_key)

        return len(jtis) if jtis else 0

    def get_token_key(self, token: str, token_type: TokenType):
        return f"{token_type}:{token}"

    async def store_token(
        self,
        token: str,
        user_id: str,
        token_type: TokenType,
        expires_in: timedelta = timedelta(seconds=settings.MAIL_TOKEN_EXPIRE_SECONDS),
    ):
        key = self.get_token_key(token, token_type)
        await self.redis.set(key, user_id, ex=expires_in)

    async def verify_token(
        self,
        token: str,
        token_type: TokenType,
    ):
        key = self.get_token_key(token, token_type)
        user_id = await self.redis.get(key)
        if not user_id:
            return None
        return user_id

    async def delete_token(
        self,
        token: str,
        token_type: TokenType,
    ):
        key = self.get_token_key(token, token_type)
        await self.redis.delete(key)


redis_client = RedisService()


def get_redis():
    return redis_client


RedisDep = Annotated[RedisService, Depends(get_redis)]
