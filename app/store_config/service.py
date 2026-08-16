from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.store_config.model import StoreConfig
from app.store_config.schema import StoreConfigUpdate

STORE_CONFIG_ID = 1


class StoreConfigService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> StoreConfig:
        config = await self.session.get(StoreConfig, STORE_CONFIG_ID)

        if not config:
            raise EntityNotFoundError(
                error_code="STORE_CONFIG_NOT_FOUND",
                message="Store settings are not configured.",
            )

        return config

    async def update(self, data: StoreConfigUpdate) -> StoreConfig:
        config = await self.get()

        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(config, field, value)

        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)

        return config
