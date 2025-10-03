from fastapi import APIRouter, status, Query
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
    PaginatedPizzaResponse,
)
from app.auth.dependencies import AdminOnlyDep
from app.menu.service import PizzaService, ToppingService, SizeService, CrustService
from app.menu.model import PizzaCategory

menu_router = APIRouter(prefix="/menu", tags=["Menu"])


# ===========================================================
# PIZZA ROUTES
# ===========================================================


@menu_router.get(
    "/pizzas",
    response_model=PaginatedPizzaResponse,
    status_code=status.HTTP_200_OK,
)
async def get_all_pizzas(
    session: SessionDep,
    page: int = Query(
        default=1,
        ge=1,
        description="Page Number",
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=100,
        description="Items per page",
    ),
    sort_by: str = Query(
        default="created_at:asc",
        description="Sort field and order (field:asc | desc)",
    ),
    name: str | None = Query(
        default=None,
        description="Filter by pizza name",
    ),
    category: PizzaCategory | None = Query(
        default=None,
        description="Filter by pizza category: veg | non_veg",
    ),
    is_available: bool | None = Query(
        default=None,
        description="Filter by availability",
    ),
    featured: bool | None = Query(
        default=None,
        description="Is featured pizza or not",
    ),
):
    """Get all pizzas with pagination, sorting, and filtering options"""
    return await PizzaService(session).get_all(
        page=page,
        limit=limit,
        sort_by=sort_by,
        name=name,
        category=category,
        is_available=is_available,
        featured=featured,
    )


@menu_router.post(
    "/pizzas",
    response_model=PizzaResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_pizza(
    pizza_data: PizzaCreate,
    session: SessionDep,
    _: AdminOnlyDep,
):
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
    pizza_id: UUID,
    pizza_data: PizzaUpdate,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to update pizza details.
    """
    return await PizzaService(session).update(pizza_id, pizza_data)


@menu_router.delete("/pizzas/{pizza_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pizza(
    pizza_id: UUID,
    session: SessionDep,
    _: AdminOnlyDep,
):
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
    category: str | None = Query(
        default=None,
        description="Filter by topping-category like meat, cheese, vegetable, etc",
    ),
    vegetarian_only: bool | None = Query(
        default=None,
        description="True returns veg toppings, False returns non-veg toppings",
    ),
    is_available: bool | None = Query(
        default=None,
        description="Filter by availability",
    ),
):
    """
    Get all available toppings for public viewing.
    Filter by category (meat, vegetable, cheese, sauce, etc) or vegetarian options.
    """
    return await ToppingService(session).get_all(
        category=category,
        vegetarian_only=vegetarian_only,
        is_available=is_available,
    )


@menu_router.post(
    "/toppings",
    response_model=ToppingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_topping(
    topping_data: ToppingCreate,
    session: SessionDep,
    _: AdminOnlyDep,
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
    _: AdminOnlyDep,
):
    """
    Admin endpoint to update topping details, pricing, or availability.
    """
    return await ToppingService(session).update(topping_id, topping_data)


@menu_router.delete("/toppings/{topping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topping(
    topping_id: UUID,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to remove topping.
    """
    return await ToppingService(session).delete(topping_id)


# ===========================================================
# SIZES ROUTES
# ===========================================================


@menu_router.get("/sizes", response_model=list[SizeResponse])
async def get_all_sizes(
    session: SessionDep,
    available_only: bool = False,
):
    """
    Get all pizza sizes with pricing multipliers.
    """
    return await SizeService(session).get_all(available_only=available_only)


@menu_router.post(
    "/sizes", response_model=SizeResponse, status_code=status.HTTP_201_CREATED
)
async def create_size(
    size_data: SizeCreate,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to add new pizza size option.
    """
    return await SizeService(session).create(size_data)


@menu_router.patch("/sizes/{size_id}", response_model=SizeResponse)
async def update_size(
    size_id: UUID,
    size_data: SizeUpdate,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to update size details or pricing multiplier.
    """
    return await SizeService(session).update(size_id, size_data)


@menu_router.delete("/sizes/{size_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_size(
    size_id: UUID,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to remove size option.
    """
    return await SizeService(session).delete(size_id)


# ===========================================================
# CRUST ROUTES
# ===========================================================


@menu_router.get("/crusts", response_model=list[CrustResponse])
async def get_all_crusts(
    session: SessionDep,
    available_only: bool = False,
):
    """
    Get all crust options with pricing adjustments.
    """
    return await CrustService(session).get_all(available_only=available_only)


@menu_router.post(
    "/crusts", response_model=CrustResponse, status_code=status.HTTP_201_CREATED
)
async def create_crust(
    crust_data: CrustCreate,
    session: SessionDep,
    _: AdminOnlyDep,
):
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
    crust_id: UUID,
    crust_data: CrustUpdate,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to update crust details or pricing.
    """
    return await CrustService(session).update(crust_id, crust_data)


@menu_router.delete("/crusts/{crust_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crust(
    crust_id: UUID,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Admin endpoint to remove crust option.
    """
    return await CrustService(session).delete(crust_id)
