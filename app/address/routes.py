from fastapi import APIRouter, status
from app.core.database import SessionDep
from app.address.schema import AddressCreate, AddressResponse, AddressUpdate
from app.auth.dependencies import UserOrAdminDep
from app.address.service import AddressesService
from uuid import UUID

address_router = APIRouter(prefix="/addresses", tags=["Addresses"])


@address_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=AddressResponse
)
async def create_address(
    session: SessionDep, address_data: AddressCreate, user: UserOrAdminDep
):
    """Create and add new address for an user"""
    return await AddressesService(session=session).create(data=address_data, user=user)


@address_router.get("/", response_model=list[AddressResponse])
async def get_addresses(session: SessionDep, user: UserOrAdminDep):
    """List all addresses of a user"""
    return await AddressesService(session=session).get_all(user=user)


@address_router.patch("/{address_id}", response_model=AddressResponse)
async def update_address(
    address_id: UUID,
    session: SessionDep,
    address_data: AddressUpdate,
    user: UserOrAdminDep,
):
    """Update one address"""
    return await AddressesService(session=session).update(
        address_id=address_id, data=address_data, user=user
    )


@address_router.delete("/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    address_id: UUID,
    session: SessionDep,
    user: UserOrAdminDep,
):
    """Delete one address"""
    return await AddressesService(session=session).delete(
        address_id=address_id, user=user
    )
