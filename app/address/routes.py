from uuid import UUID

from fastapi import APIRouter, status

from app.address.schema import AddressCreate, AddressResponse, AddressUpdate
from app.auth.dependencies import CurrentUserDep

from .dependencies import AddressServiceDep

address_router = APIRouter(prefix="/addresses", tags=["Addresses"])


@address_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=AddressResponse,
)
async def create_address(
    address_service: AddressServiceDep,
    address_data: AddressCreate,
    user: CurrentUserDep,
):
    """Create and add new address for an user"""
    return await address_service.create(
        data=address_data,
        user_id=user.id,
    )


@address_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=list[AddressResponse],
)
async def get_addresses(
    address_service: AddressServiceDep,
    user: CurrentUserDep,
):
    """List all addresses of a user"""
    return await address_service.get_all(user_id=user.id)


@address_router.patch(
    "/{address_id}",
    status_code=status.HTTP_200_OK,
    response_model=AddressResponse,
)
async def update_address(
    address_id: UUID,
    address_service: AddressServiceDep,
    address_data: AddressUpdate,
    user: CurrentUserDep,
):
    """Update one address"""
    return await address_service.update(
        address_id=address_id,
        data=address_data,
        user_id=user.id,
    )


@address_router.delete(
    "/{address_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_address(
    address_id: UUID,
    address_service: AddressServiceDep,
    user: CurrentUserDep,
):
    """Delete one address"""
    return await address_service.delete(
        address_id=address_id,
        user_id=user.id,
    )
