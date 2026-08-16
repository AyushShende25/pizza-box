from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep

from .service import StoreConfigService


def get_store_config_service(session: SessionDep) -> StoreConfigService:
    """Provides a fresh StoreConfigService instance"""
    return StoreConfigService(session=session)


StoreConfigServiceDep = Annotated[StoreConfigService, Depends(get_store_config_service)]
