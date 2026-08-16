from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.menu.service import CrustService, PizzaService, SizeService, ToppingService


def get_pizza_service(session: SessionDep) -> PizzaService:
    """Provides a fresh PizzaService instance"""
    return PizzaService(session)


def get_topping_service(session: SessionDep) -> ToppingService:
    """Provides a fresh ToppingService instance"""
    return ToppingService(session)


def get_size_service(session: SessionDep) -> SizeService:
    """Provides a fresh SizeService instance"""
    return SizeService(session)


def get_crust_service(session: SessionDep) -> CrustService:
    """Provides a fresh CrustService instance"""
    return CrustService(session)


PizzaServiceDep = Annotated[PizzaService, Depends(get_pizza_service)]

ToppingServiceDep = Annotated[ToppingService, Depends(get_topping_service)]

SizeServiceDep = Annotated[SizeService, Depends(get_size_service)]

CrustServiceDep = Annotated[CrustService, Depends(get_crust_service)]
