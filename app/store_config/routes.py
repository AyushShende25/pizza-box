from fastapi import APIRouter, status

from app.auth.dependencies import AdminUserDep

from .dependencies import StoreConfigServiceDep
from .schema import (
    StoreConfigResponse,
    StoreConfigResponsePublic,
    StoreConfigUpdate,
)

store_config_router = APIRouter(
    prefix="/store-config",
    tags=["StoreConfig"],
)


@store_config_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StoreConfigResponse,
)
async def get_store_config(
    store_config_service: StoreConfigServiceDep,
    _: AdminUserDep,
):
    """Admin endpoint to fetch store config."""
    return await store_config_service.get()


@store_config_router.get(
    "/public",
    status_code=status.HTTP_200_OK,
    response_model=StoreConfigResponsePublic,
)
async def get_public_store_config(
    store_config_service: StoreConfigServiceDep,
):
    """Get Store Config"""
    return await store_config_service.get()


@store_config_router.patch(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=StoreConfigResponse,
)
async def update_store_config(
    store_config_service: StoreConfigServiceDep,
    _: AdminUserDep,
    data: StoreConfigUpdate,
):
    """
    Admin endpoint to update store config.
    """
    return await store_config_service.update(data=data)
