from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep

from .service import AddressService


def get_address_service(session: SessionDep) -> AddressService:
    """Provides a fresh AddressService instance"""
    return AddressService(session)


AddressServiceDep = Annotated[AddressService, Depends(get_address_service)]
