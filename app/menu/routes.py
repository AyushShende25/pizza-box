from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep

from .dependencies import (
    CrustServiceDep,
    PizzaServiceDep,
    SizeServiceDep,
    ToppingServiceDep,
)
from .schema import (
    CrustCreate,
    CrustQueryParams,
    CrustResponse,
    CrustUpdate,
    PaginatedPizzaResponse,
    PizzaCreate,
    PizzaQueryParams,
    PizzaResponse,
    PizzaUpdate,
    SizeCreate,
    SizeQueryParams,
    SizeResponse,
    SizeUpdate,
    ToppingCreate,
    ToppingQueryParams,
    ToppingResponse,
    ToppingUpdate,
)

menu_router = APIRouter(prefix="/menu", tags=["Menu"])


# ===========================================================
# PIZZA ROUTES
# ===========================================================


@menu_router.get(
    "/pizzas",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedPizzaResponse,
)
async def get_all_pizzas(
    pizza_service: PizzaServiceDep,
    params: Annotated[PizzaQueryParams, Query()],
):
    """Get all pizzas with pagination, sorting, and filtering options"""
    return await pizza_service.get_all(
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        order=params.order,
        food_type=params.food_type,
        name=params.name,
        is_available=params.is_available,
        is_featured=params.is_featured,
    )


@menu_router.post(
    "/pizzas",
    status_code=status.HTTP_201_CREATED,
    response_model=PizzaResponse,
)
async def create_pizza(
    data: PizzaCreate,
    pizza_service: PizzaServiceDep,
    _: AdminUserDep,
):
    """Admin endpoint to create new pizza"""
    return await pizza_service.create(data=data)


@menu_router.get(
    "/pizzas/{pizza_id}",
    status_code=status.HTTP_200_OK,
    response_model=PizzaResponse,
)
async def get_pizza_by_id(
    pizza_id: UUID,
    pizza_service: PizzaServiceDep,
):
    """
    Get detailed information about a specific pizza.
    """
    return await pizza_service.get_one(pizza_id=pizza_id)


@menu_router.patch(
    "/pizzas/{pizza_id}",
    status_code=status.HTTP_200_OK,
    response_model=PizzaResponse,
)
async def update_pizza(
    pizza_id: UUID,
    data: PizzaUpdate,
    pizza_service: PizzaServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to update pizza details.
    """
    return await pizza_service.update(pizza_id=pizza_id, data=data)


@menu_router.delete(
    "/pizzas/{pizza_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_pizza(
    pizza_id: UUID,
    pizza_service: PizzaServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to  remove a pizza from menu.
    """
    return await pizza_service.delete(pizza_id=pizza_id)


# ===========================================================
# TOPPINGS ROUTES
# ===========================================================


@menu_router.get(
    "/toppings",
    status_code=status.HTTP_200_OK,
    response_model=list[ToppingResponse],
)
async def get_all_toppings(
    topping_service: ToppingServiceDep,
    params: Annotated[ToppingQueryParams, Query()],
):
    """
    Get all toppings for public viewing.
    Filter by category (meat, vegetable, cheese, sauce, etc), availability or food-type options.
    """
    return await topping_service.get_all(
        category=params.category,
        food_type=params.food_type,
        is_available=params.is_available,
    )


@menu_router.post(
    "/toppings",
    status_code=status.HTTP_201_CREATED,
    response_model=ToppingResponse,
)
async def create_topping(
    data: ToppingCreate,
    topping_service: ToppingServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to add new topping.
    """
    return await topping_service.create(data=data)


@menu_router.get(
    "/toppings/{topping_id}",
    status_code=status.HTTP_200_OK,
    response_model=ToppingResponse,
)
async def get_topping_by_id(
    topping_id: UUID,
    topping_service: ToppingServiceDep,
):
    """
    Get details of a specific topping.
    """
    return await topping_service.get_one(topping_id=topping_id)


@menu_router.patch(
    "/toppings/{topping_id}",
    status_code=status.HTTP_200_OK,
    response_model=ToppingResponse,
)
async def update_topping(
    topping_id: UUID,
    data: ToppingUpdate,
    topping_service: ToppingServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to update topping details, pricing, or availability.
    """
    return await topping_service.update(
        topping_id=topping_id,
        data=data,
    )


@menu_router.delete(
    "/toppings/{topping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_topping(
    topping_id: UUID,
    topping_service: ToppingServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to remove topping.
    """
    return await topping_service.delete(topping_id=topping_id)


# ===========================================================
# SIZES ROUTES
# ===========================================================


@menu_router.get(
    "/sizes",
    status_code=status.HTTP_200_OK,
    response_model=list[SizeResponse],
)
async def get_all_sizes(
    size_service: SizeServiceDep,
    params: Annotated[SizeQueryParams, Query()],
):
    """
    Get all pizza sizes with pricing multipliers.
    """
    return await size_service.get_all(
        is_available=params.is_available,
    )


@menu_router.post(
    "/sizes",
    status_code=status.HTTP_201_CREATED,
    response_model=SizeResponse,
)
async def create_size(
    data: SizeCreate,
    size_service: SizeServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to add new pizza size option.
    """
    return await size_service.create(data=data)


@menu_router.patch(
    "/sizes/{size_id}",
    status_code=status.HTTP_200_OK,
    response_model=SizeResponse,
)
async def update_size(
    size_id: UUID,
    data: SizeUpdate,
    size_service: SizeServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to update size details or pricing multiplier.
    """
    return await size_service.update(
        size_id=size_id,
        data=data,
    )


@menu_router.delete(
    "/sizes/{size_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_size(
    size_id: UUID,
    size_service: SizeServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to remove size option.
    """
    return await size_service.delete(size_id=size_id)


# ===========================================================
# CRUST ROUTES
# ===========================================================


@menu_router.get(
    "/crusts",
    status_code=status.HTTP_200_OK,
    response_model=list[CrustResponse],
)
async def get_all_crusts(
    crust_service: CrustServiceDep,
    params: Annotated[CrustQueryParams, Query()],
):
    """
    Get all crust options with pricing adjustments.
    """
    return await crust_service.get_all(
        is_available=params.is_available,
    )


@menu_router.post(
    "/crusts",
    status_code=status.HTTP_201_CREATED,
    response_model=CrustResponse,
)
async def create_crust(
    data: CrustCreate,
    crust_service: CrustServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to add new crust option.
    """
    return await crust_service.create(data=data)


@menu_router.get(
    "/crusts/{crust_id}",
    status_code=status.HTTP_200_OK,
    response_model=CrustResponse,
)
async def get_crust_by_id(
    crust_id: UUID,
    crust_service: CrustServiceDep,
):
    """
    Get details of a specific crust.
    """
    return await crust_service.get_one(crust_id=crust_id)


@menu_router.patch(
    "/crusts/{crust_id}",
    status_code=status.HTTP_200_OK,
    response_model=CrustResponse,
)
async def update_crust(
    crust_id: UUID,
    data: CrustUpdate,
    crust_service: CrustServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to update crust details or pricing.
    """
    return await crust_service.update(
        crust_id=crust_id,
        data=data,
    )


@menu_router.delete(
    "/crusts/{crust_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_crust(
    crust_id: UUID,
    crust_service: CrustServiceDep,
    _: AdminUserDep,
):
    """
    Admin endpoint to remove crust option.
    """
    return await crust_service.delete(crust_id=crust_id)
