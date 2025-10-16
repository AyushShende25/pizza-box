from fastapi import APIRouter, status
from app.core.database import SessionDep
from app.address.schema import AddressCreate, AddressResponse
from app.auth.dependencies import UserOrAdminDep
from app.address.service import AddressesService

address_router = APIRouter(prefix="/addresses", tags=["Addresses"])


@address_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=AddressResponse
)
async def create_address(
    session: SessionDep, address_data: AddressCreate, user: UserOrAdminDep
):
    return await AddressesService(session=session).create(data=address_data, user=user)
