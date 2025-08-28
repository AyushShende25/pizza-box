from fastapi import APIRouter, status
from uuid import UUID
from app.core.database import SessionDep
from app.menu.schema import (
    PizzaCreate,
    PizzaResponse,
    PizzaUpdate,
    ToppingResponse,
    ToppingCreate,
    ToppingUpdate,
    SizeResponse,
    SizeCreate,
    SizeUpdate,
    CrustResponse,
    CrustCreate,
    CrustUpdate,
)
from app.auth.dependencies import AdminOnlyDep
from app.menu.service import PizzaService, ToppingService, SizeService, CrustService

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


# ===========================================================
# TOPPINGS ROUTES
# ===========================================================


@menu_router.get("/toppings", response_model=list[ToppingResponse])
async def get_all_toppings(
    session: SessionDep,
    category: str | None = None,
    vegetarian_only: bool | None = None,
):
    """
    Get all available toppings for public viewing.
    Filter by category (meat, vegetable, cheese, sauce, etc) or vegetarian options.
    """
    return await ToppingService(session).get_all(category, vegetarian_only)


@menu_router.post(
    "/toppings",
    response_model=ToppingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_topping(
    topping_data: ToppingCreate,
    session: SessionDep,
    # _: AdminOnlyDep,
):
    """
    Admin endpoint to add new topping.
    """
    return await ToppingService(session).create(topping_data)


@menu_router.get("/toppings/{topping_id}", response_model=ToppingResponse)
async def get_topping_by_id(topping_id: UUID, session: SessionDep):
    """
    Get details of a specific topping.
    """
    return await ToppingService(session).get_one(topping_id)


@menu_router.patch("/toppings/{topping_id}", response_model=ToppingResponse)
async def update_topping(
    topping_id: UUID,
    topping_data: ToppingUpdate,
    session: SessionDep,
    # _: AdminOnlyDep,
):
    """
    Admin endpoint to update topping details, pricing, or availability.
    """
    return await ToppingService(session).update(topping_id, topping_data)


@menu_router.delete("/toppings/{topping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topping(
    topping_id: UUID,
    session: SessionDep,
    # _: AdminOnlyDep,
):
    """
    Admin endpoint to remove topping.
    """
    return await ToppingService(session).delete(topping_id)


# ===========================================================
# SIZES ROUTES
# ===========================================================


@menu_router.get("/sizes", response_model=list[SizeResponse])
async def get_all_sizes(session: SessionDep):
    """
    Get all available pizza sizes with pricing multipliers.
    """
    return await SizeService(session).get_all()


@menu_router.post(
    "/sizes", response_model=SizeResponse, status_code=status.HTTP_201_CREATED
)
async def create_size(size_data: SizeCreate, session: SessionDep, _: AdminOnlyDep):
    """
    Admin endpoint to add new pizza size option.
    """
    return await SizeService(session).create(size_data)


@menu_router.patch("/sizes/{size_id}", response_model=SizeResponse)
async def update_size(
    size_id: UUID, size_data: SizeUpdate, session: SessionDep, _: AdminOnlyDep
):
    """
    Admin endpoint to update size details or pricing multiplier.
    """
    return await SizeService(session).update(size_id, size_data)


@menu_router.delete("/sizes/{size_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_size(size_id: UUID, session: SessionDep, _: AdminOnlyDep):
    """
    Admin endpoint to remove size option.
    """
    return await SizeService(session).delete(size_id)


# ===========================================================
# CRUST ROUTES
# ===========================================================


@menu_router.get("/crusts", response_model=list[CrustResponse])
async def get_all_crusts(session: SessionDep):
    """
    Get all available crust options with pricing adjustments.
    """
    return await CrustService(session).get_all()


@menu_router.post(
    "/crusts", response_model=CrustResponse, status_code=status.HTTP_201_CREATED
)
async def create_crust(crust_data: CrustCreate, session: SessionDep, _: AdminOnlyDep):
    """
    Admin endpoint to add new crust option.
    """
    return await CrustService(session).create(crust_data)


@menu_router.get("/crusts/{crust_id}", response_model=CrustResponse)
async def get_crust_by_id(crust_id: UUID, session: SessionDep):
    """
    Get details of a specific crust.
    """
    return await CrustService(session).get_one(crust_id)


@menu_router.patch("/crusts/{crust_id}", response_model=CrustResponse)
async def update_crust(
    crust_id: UUID, crust_data: CrustUpdate, session: SessionDep, _: AdminOnlyDep
):
    """
    Admin endpoint to update crust details or pricing.
    """
    return await CrustService(session).update(crust_id, crust_data)


@menu_router.delete("/crusts/{crust_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crust(crust_id: UUID, session: SessionDep, _: AdminOnlyDep):
    """
    Admin endpoint to remove crust option.
    """
    return await CrustService(session).delete(crust_id)
