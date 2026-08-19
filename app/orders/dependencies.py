from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep

from .service import OrderService


def get_order_service(session: SessionDep) -> OrderService:
    """Provides a fresh OrderService instance"""
    return OrderService(session)


OrderServiceDep = Annotated[OrderService, Depends(get_order_service)]
