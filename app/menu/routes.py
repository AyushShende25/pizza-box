from fastapi import APIRouter, status
from uuid import UUID
from app.core.database import SessionDep
from app.menu.schema import PizzaCreate, PizzaResponse, PizzaUpdate
from app.auth.dependencies import AdminOnlyDep
from app.menu.service import PizzaService

menu_router = APIRouter(prefix="/menu", tags=["Menu"])


# ===========================================================
# PIZZA ROUTES
# ===========================================================


@menu_router.get(
    "/pizzas",
    response_model=list[PizzaResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_pizzas(session: SessionDep):
    """Get all pizzas"""
    return await PizzaService(session).get_all()


@menu_router.post(
    "/pizzas",
    response_model=PizzaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pizza(pizza_data: PizzaCreate, session: SessionDep, _: AdminOnlyDep):
    """Admin endpoint to create new pizza"""
    return await PizzaService(session).create(pizza_data)


@menu_router.get(
    "/pizzas/{pizza_id}",
    response_model=PizzaResponse,
    status_code=status.HTTP_200_OK,
)
async def get_pizza_by_id(pizza_id: UUID, session: SessionDep):
    """
    Get detailed information about a specific pizza.
    """
    return await PizzaService(session).get_one(pizza_id)


@menu_router.patch("/pizzas/{pizza_id}", response_model=PizzaResponse)
async def update_pizza(
    pizza_id: UUID, pizza_data: PizzaUpdate, session: SessionDep, _: AdminOnlyDep
):
    """
    Admin endpoint to update pizza details.
    """
    return await PizzaService(session).update(pizza_id, pizza_data)


@menu_router.delete("/pizzas/{pizza_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pizza(pizza_id: UUID, session: SessionDep, _: AdminOnlyDep):
    """
    Admin endpoint to  remove a pizza from menu.
    """
    return await PizzaService(session).delete(pizza_id)
