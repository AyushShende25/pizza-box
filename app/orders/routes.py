from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, status

from app.auth.dependencies import AdminUserDep, CurrentUserDep

from .dependencies import OrderServiceDep
from .schema import (
    AdminOrderQueryParams,
    OrderCreate,
    OrderMonthlySalesQueryParams,
    OrderResponse,
    OrderStatsQueryParams,
    OrderUpdate,
    PaginatedOrderResponse,
    UserOrderQueryParams,
)

orders_router = APIRouter(prefix="/orders", tags=["Orders"])


@orders_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderResponse,
)
async def create_new_order(
    order_service: OrderServiceDep,
    data: OrderCreate,
    current_user: CurrentUserDep,
):
    """Create new order with PENDING state"""
    return await order_service.create_order(
        data=data,
        user=current_user,
    )


@orders_router.get(
    "/my-orders",
    status_code=status.HTTP_200_OK,
    response_model=list[OrderResponse],
)
async def get_my_orders(
    order_service: OrderServiceDep,
    current_user: CurrentUserDep,
    order_params: Annotated[UserOrderQueryParams, Query()],
):
    """Get all orders for current user"""
    return await order_service.get_user_orders(
        user_id=current_user.id,
        page=order_params.page,
        limit=order_params.limit,
        order_status=order_params.order_status,
        payment_status=order_params.payment_status,
    )


@orders_router.get(
    "/my-orders/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=OrderResponse,
)
async def get_my_order_detail(
    order_id: UUID,
    order_service: OrderServiceDep,
    current_user: CurrentUserDep,
):
    """Get specific order details for current user"""
    return await order_service.get_user_order(
        user_id=current_user.id,
        order_id=order_id,
    )


@orders_router.post(
    "/my-orders/{order_id}/cancel",
    status_code=status.HTTP_200_OK,
    response_model=OrderResponse,
)
async def cancel_my_order(
    order_id: UUID,
    order_service: OrderServiceDep,
    current_user: CurrentUserDep,
):
    """
    Cancel current-user order (only if PENDING)
    """
    return await order_service.cancel_user_order(
        user_id=current_user.id,
        order_id=order_id,
    )


@orders_router.patch(
    "/{order_id}/status",
    status_code=status.HTTP_200_OK,
    response_model=OrderResponse,
)
async def update_order_status(
    order_id: UUID,
    data: OrderUpdate,
    order_service: OrderServiceDep,
    _: AdminUserDep,
):
    """
    Update order status (ADMIN route)
    E.g., CONFIRMED → PREPARING → OUT_FOR_DELIVERY → DELIVERED
    """
    return await order_service.update_order_status(
        order_id=order_id,
        order_status=data.order_status,
    )


@orders_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=PaginatedOrderResponse,
)
async def get_all_orders(
    order_service: OrderServiceDep,
    _: AdminUserDep,
    params: Annotated[AdminOrderQueryParams, Query()],
):
    """Get all orders (ADMIN route)"""
    return await order_service.get_all_orders(
        page=params.page,
        limit=params.limit,
        sort_by=params.sort_by,
        sort_order=params.sort_order,
        order_status=params.order_status,
        payment_status=params.payment_status,
        payment_method=params.payment_method,
    )


@orders_router.get(
    "/{order_id}",
    status_code=status.HTTP_200_OK,
    response_model=OrderResponse,
)
async def get_order_detail(
    order_id: UUID,
    order_service: OrderServiceDep,
    _: AdminUserDep,
):
    """Get specific order details (ADMIN route)"""
    return await order_service.get_order(
        order_id=order_id,
    )


@orders_router.get(
    "/stats/summary",
    status_code=status.HTTP_200_OK,
)
async def get_order_statistics(
    order_service: OrderServiceDep,
    _: AdminUserDep,
    data: Annotated[OrderStatsQueryParams, Query()],
):
    """
    Get order statistics (admin only)
    - Total orders, sales
    - Orders by status
    - Popular pizzas.
    """

    totals = await order_service.get_order_stats(data.start_date, data.end_date)

    status_breakdown = await order_service.get_orders_by_status(
        data.start_date, data.end_date
    )

    top_pizzas = await order_service.get_top_selling_pizzas(
        data.start_date, data.end_date, data.limit
    )

    return {
        **totals,
        "orders_by_status": status_breakdown,
        "top_pizzas": top_pizzas,
    }


@orders_router.get(
    "/stats/monthly-sales",
    status_code=status.HTTP_200_OK,
)
async def get_monthly_sales(
    order_service: OrderServiceDep,
    _: AdminUserDep,
    data: Annotated[OrderMonthlySalesQueryParams, Query()],
):
    return await order_service.get_monthly_sales(data.months_count)
