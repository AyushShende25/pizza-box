from datetime import timedelta
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.auth.schema import MailTokenType
from app.core.config import settings
from app.libs.redis import redis_client

# Individual Session Key (String)
# refresh:<session_id> -> <user_id>

# User's Active Sessions Index (Set)
# user_refresh:<user_id> -> { <session_id_1>, <session_id_2>, ... }

# Single-use Mail Token (String)
# <token_type>:<token> -> <user_id>


class AuthRedisRepository:
    def __init__(self, client: redis.Redis):
        self.redis = client

    def _refresh_token_key(self, session_id: str) -> str:
        return f"refresh:{session_id}"

    def _user_refresh_tokens_key(self, user_id: str) -> str:
        return f"user_refresh:{user_id}"

    def _mail_token_key(self, token: str, token_type: MailTokenType) -> str:
        return f"{token_type}:{token}"

    async def create_refresh_session(
        self,
        session_id: str,
        user_id: str,
        expires_in: timedelta = timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
    ) -> None:
        """Create a refresh-token session"""
        refresh_key = self._refresh_token_key(session_id)
        user_set_key = self._user_refresh_tokens_key(user_id)

        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.set(refresh_key, user_id, ex=expires_in)
            pipe.sadd(user_set_key, session_id)
            pipe.expire(user_set_key, expires_in)
            await pipe.execute()

    async def get_refresh_session_user(self, session_id: str) -> str | None:
        """Return the user ID associated with a refresh session."""
        key = self._refresh_token_key(session_id)
        return await self.redis.get(key)

    async def delete_refresh_session(self, session_id: str) -> None:
        """Revoke session"""
        refresh_key = self._refresh_token_key(session_id)
        user_id = await self.redis.get(refresh_key)

        async with self.redis.pipeline(transaction=True) as pipe:
            if user_id:
                pipe.srem(self._user_refresh_tokens_key(user_id), session_id)
            pipe.delete(refresh_key)
            await pipe.execute()

    async def delete_all_refresh_sessions(self, user_id: str) -> int:
        """Revoke all sessions for a specific user."""
        user_session_ids_key = self._user_refresh_tokens_key(user_id)

        # Get all session_ids for this user
        session_ids = await self.redis.smembers(user_session_ids_key)

        if not session_ids:
            return 0

        token_id_keys = [
            self._refresh_token_key(session_id) for session_id in session_ids
        ]
        if token_id_keys:
            async with self.redis.pipeline(transaction=True) as pipe:
                pipe.delete(*token_id_keys)
                pipe.delete(user_session_ids_key)
                await pipe.execute()

        return len(session_ids)

    async def store_mail_token(
        self,
        token: str,
        user_id: str,
        token_type: MailTokenType,
        expires_in: timedelta = timedelta(seconds=settings.MAIL_TOKEN_EXPIRE_SECONDS),
    ) -> None:
        """Store a single-use email verification or password reset token"""
        key = self._mail_token_key(token, token_type)
        await self.redis.set(key, user_id, ex=expires_in)

    async def get_mail_token_user(
        self,
        token: str,
        token_type: MailTokenType,
    ) -> str | None:
        """Validate and fetch the user ID associated with mail token"""
        key = self._mail_token_key(token, token_type)
        return await self.redis.get(key)

    async def delete_mail_token(
        self,
        token: str,
        token_type: MailTokenType,
    ) -> None:
        """Delete mail token immediately after successful consumption"""
        key = self._mail_token_key(token, token_type)
        await self.redis.delete(key)


auth_redis_repository = AuthRedisRepository(redis_client)


def get_auth_redis_repository() -> AuthRedisRepository:
    return auth_redis_repository


AuthRedisRepositoryDep = Annotated[
    AuthRedisRepository, Depends(get_auth_redis_repository)
]
