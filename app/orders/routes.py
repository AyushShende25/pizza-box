from fastapi import APIRouter, status, Query
from uuid import UUID
from typing import Annotated
from app.auth.dependencies import AdminOnlyDep, UserOrAdminDep
from app.core.database import SessionDep
from app.orders.schema import (
    OrderCreate,
    OrderResponse,
    OrderUpdate,
    PaginatedOrderResponse,
    UserOrderQueryParams,
    AdminOrderQueryParams,
    OrderStatsQueryParams,
    OrderMonthlySalesQueryParams,
)
from app.orders.service import OrderService

orders_router = APIRouter(prefix="/orders", tags=["Orders"])


@orders_router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    response_model=OrderResponse,
)
async def create_new_order(
    session: SessionDep,
    order_data: OrderCreate,
    current_user: UserOrAdminDep,
):
    """Create new order with PENDING state"""
    return await OrderService(session=session).create_order(
        data=order_data, user_id=current_user.id
    )


@orders_router.get("/my-orders", response_model=list[OrderResponse])
async def get_my_orders(
    session: SessionDep,
    current_user: UserOrAdminDep,
    order_params: Annotated[UserOrderQueryParams, Query()],
):
    """Get all orders for current user"""
    return await OrderService(session=session).get_user_orders(
        user_id=current_user.id,
        page=order_params.page,
        limit=order_params.limit,
        order_status=order_params.order_status,
        payment_status=order_params.payment_status,
    )


@orders_router.get("/my-orders/{order_id}", response_model=OrderResponse)
async def get_my_order_detail(
    order_id: UUID,
    session: SessionDep,
    current_user: UserOrAdminDep,
):
    """Get specific order details for current user"""
    return await OrderService(session=session).get_user_order(
        user_id=current_user.id, order_id=order_id
    )


@orders_router.post("/my-orders/{order_id}/cancel", response_model=OrderResponse)
async def cancel_my_order(
    order_id: UUID,
    session: SessionDep,
    current_user: UserOrAdminDep,
):
    """
    Cancel current-user order (only if PENDING)
    """
    return await OrderService(session=session).cancel_user_order(
        user_id=current_user.id, order_id=order_id
    )


@orders_router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    order_data: OrderUpdate,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """
    Update order status (ADMIN route)
    E.g., CONFIRMED → PREPARING → OUT_FOR_DELIVERY → DELIVERED
    """
    return await OrderService(session=session).update_order_status(
        order_id=order_id,
        order_status=order_data.order_status,
    )


@orders_router.get("/", response_model=PaginatedOrderResponse)
async def get_all_orders(
    session: SessionDep,
    _: AdminOnlyDep,
    order_params: Annotated[AdminOrderQueryParams, Query()],
):
    """Get all orders (ADMIN route)"""
    return await OrderService(session=session).get_all_orders(
        page=order_params.page,
        limit=order_params.limit,
        sort_by=order_params.sort_by,
        order_status=order_params.order_status,
        payment_status=order_params.payment_status,
        payment_method=order_params.payment_method,
    )


@orders_router.get("/{order_id}", response_model=OrderResponse)
async def get_order_detail(
    order_id: UUID,
    session: SessionDep,
    _: AdminOnlyDep,
):
    """Get specific order details (ADMIN route)"""
    return await OrderService(session=session).get_order(
        order_id=order_id,
    )


@orders_router.get("/stats/summary")
async def get_order_statistics(
    session: SessionDep,
    _: AdminOnlyDep,
    data: Annotated[OrderStatsQueryParams, Query()],
):
    """
    Get order statistics (admin only)
    - Total orders, sales
    - Orders by status
    - Popular pizzas.
    """
    order_service = OrderService(session)

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


@orders_router.get("/stats/monthly-sales")
async def get_monthly_sales(
    session: SessionDep,
    _: AdminOnlyDep,
    data: Annotated[OrderMonthlySalesQueryParams, Query()],
):
    return await OrderService(session).get_monthly_sales(data.months_count)
