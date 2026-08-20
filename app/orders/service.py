import math
from datetime import date, timedelta
from decimal import Decimal
from typing import ClassVar
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.address.service import AddressService
from app.auth.model import User
from app.cart.service import CartService
from app.core.exceptions import BadRequestError, EntityNotFoundError
from app.notifications.events import publish_order_event
from app.notifications.schema import OrderEventData
from app.store_config.service import StoreConfigService

from .model import (
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from .schema import OrderCreate, OrderSortField, SortOrder
from .utils import generate_order_num

ORDER_STATUS_MESSAGES = {
    OrderStatus.CONFIRMED: "Restaurant has confirmed your order.",
    OrderStatus.PREPARING: "Your pizza is being prepared!",
    OrderStatus.OUT_FOR_DELIVERY: "Your order is on its way!",
    OrderStatus.DELIVERED: "Your order has been delivered!",
    OrderStatus.CANCELLED: "Your order has been cancelled.",
}


class OrderService:
    SORT_MAP: ClassVar[dict[OrderSortField, InstrumentedAttribute]] = {
        "created_at": Order.created_at,
        "order_no": Order.order_no,
        "total": Order.total,
    }

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def load_order(self, order_id: UUID) -> Order:
        stmt = (
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.toppings))
            .where(Order.id == order_id)
        )

        result = await self.session.execute(stmt)

        order = result.scalar_one_or_none()

        if order is None:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Order does not exist",
            )

        return order

    async def create_order(
        self,
        data: OrderCreate,
        user: User,
    ) -> Order:
        store_config = await StoreConfigService(session=self.session).get()

        if not store_config.is_accepting_orders:
            raise BadRequestError(
                error_code="STORE_CLOSED",
                message="We are currently not accepting orders",
            )

        cart = await CartService(session=self.session).get_user_cart(user_id=user.id)

        if not cart:
            raise EntityNotFoundError(
                error_code="CART_NOT_FOUND",
                message="cart not found",
            )

        address = await AddressService(self.session).get_one(
            address_id=data.address_id,
            user_id=user.id,
        )

        order_status = (
            OrderStatus.CONFIRMED
            if data.payment_method == PaymentMethod.COD
            else OrderStatus.PENDING
        )

        order = Order(
            order_no=generate_order_num(),
            user_id=user.id,
            customer_name=f"{user.first_name} {user.last_name}",
            address_id=data.address_id,
            notes=data.notes,
            payment_method=data.payment_method,
            delivery_name=address.full_name,
            delivery_phone=address.phone_number,
            delivery_street=address.street,
            delivery_city=address.city,
            delivery_state=address.state,
            delivery_postal_code=address.postal_code,
            delivery_country=address.country,
            subtotal=cart.subtotal,
            tax=cart.tax,
            delivery_charge=cart.delivery_charge,
            total=cart.total,
            order_status=order_status,
        )

        for cart_item in cart.cart_items:
            if (
                not cart_item.pizza.is_available
                or not cart_item.size.is_available
                or not cart_item.crust.is_available
            ):
                raise BadRequestError(
                    error_code="ITEM_UNAVAILABLE",
                    message="One or more selected items are unavailable",
                )

            if any(not topping.is_available for topping in cart_item.toppings):
                raise BadRequestError(
                    error_code="TOPPING_UNAVAILABLE",
                    message="One or more selected toppings are unavailable",
                )

            order_item = OrderItem(
                pizza_id=cart_item.pizza.id,
                size_id=cart_item.size.id,
                crust_id=cart_item.crust.id,
                pizza_name=cart_item.pizza.name,
                size_name=cart_item.size.name,
                crust_name=cart_item.crust.name,
                size_price_modifier=cart_item.size.price_modifier,
                crust_price_modifier=cart_item.crust.price_modifier,
                base_pizza_price=cart_item.pizza.base_price,
                toppings_total_price=cart_item.toppings_total_price,
                unit_price=cart_item.unit_price,
                total_price=cart_item.total,
                quantity=cart_item.quantity,
            )

            for topping in cart_item.toppings:
                order_item.toppings.append(
                    OrderItemTopping(
                        topping_id=topping.id,
                        topping_name=topping.name,
                        topping_price=topping.price_modifier,
                    )
                )

            order.order_items.append(order_item)

        if order.subtotal < store_config.min_order_value:
            raise BadRequestError(
                error_code="BELOW_MIN_ORDER_VALUE",
                message=f"Minimum order value is {store_config.min_order_value}",
            )

        self.session.add(order)

        await CartService(session=self.session).clear_cart(cart_id=cart.id)

        await self.session.commit()

        await publish_order_event(
            event_type="order_created",
            data=OrderEventData(
                order_id=order.id,
                order_num=order.order_no,
                user_id=order.user_id,
                status=order.order_status,
                payment_status=order.payment_status,
                total_amount=order.total,
            ),
        )

        loaded_order = await self.load_order(order.id)
        return loaded_order

    async def get_user_orders(
        self,
        user_id: UUID,
        page: int,
        limit: int,
        order_status: OrderStatus | None = None,
        payment_status: PaymentStatus | None = None,
    ) -> list[Order]:
        skip = (page - 1) * limit

        base_query, _ = self._build_queries(
            order_status=order_status,
            payment_status=payment_status,
        )

        stmt = (
            base_query
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .offset(skip)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_user_order(
        self,
        user_id: UUID,
        order_id: UUID,
    ) -> Order:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
        )

        order = result.scalar_one_or_none()

        if not order:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Order with that id does not exist",
            )

        return order

    async def get_order(
        self,
        order_id: UUID,
    ) -> Order:
        result = await self.session.execute(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
        )

        order = result.scalar_one_or_none()

        if not order:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Order with that id does not exist",
            )

        return order

    async def cancel_user_order(
        self,
        user_id: UUID,
        order_id: UUID,
    ):
        order = await self.get_user_order(
            user_id=user_id,
            order_id=order_id,
        )

        if order.order_status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise BadRequestError(
                error_code="ORDER_CANCEL_FAILURE",
                message="Cannot cancel order in current status",
            )

        if order.payment_status == PaymentStatus.PAID:
            raise BadRequestError(
                error_code="ORDER_CANCEL_FAILURE",
                message="Cannot cancel paid order. Please request refund",
            )

        order.order_status = OrderStatus.CANCELLED

        await self.session.commit()
        await self.session.refresh(order)

        await publish_order_event(
            event_type="order_cancelled",
            data=OrderEventData(
                order_id=order.id,
                order_num=order.order_no,
                user_id=order.user_id,
                status=OrderStatus.CANCELLED,
                payment_status=order.payment_status,
                total_amount=order.total,
                reason="User cancelled before preparation",
            ),
        )

        return order

    async def get_all_orders(
        self,
        page: int,
        limit: int,
        sort_by: OrderSortField,
        sort_order: SortOrder,
        order_status: OrderStatus | None = None,
        payment_status: PaymentStatus | None = None,
        payment_method: PaymentMethod | None = None,
    ):
        skip = (page - 1) * limit

        base_query, count_query = self._build_queries(
            order_status=order_status,
            payment_status=payment_status,
            payment_method=payment_method,
        )

        sort_column = self.SORT_MAP[sort_by]
        order_by = (
            asc(sort_column) if sort_order.lower() == "asc" else desc(sort_column)
        )

        result = await self.session.execute(count_query)
        total = result.scalar_one() or 0

        result = await self.session.execute(
            base_query
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
            .order_by(order_by)
            .limit(limit)
            .offset(skip)
        )
        items = result.scalars().all()

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total > 0 else 0,
        }

    async def update_order_status(
        self,
        order_id: UUID,
        order_status: OrderStatus,
    ) -> Order:
        result = await self.session.execute(select(Order).where(Order.id == order_id))

        order = result.scalar_one_or_none()

        if not order:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Order with that id does not exist",
            )

        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.OUT_FOR_DELIVERY],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
        }

        if order_status not in valid_transitions.get(order.order_status, []):
            raise BadRequestError(
                error_code="ORDER_STATUS_UPDATE_ERROR",
                message=f"Cannot transition from {order.order_status.value} to {order_status.value}",
            )

        order.order_status = order_status
        await self.session.commit()

        status_message = ORDER_STATUS_MESSAGES.get(
            order_status, f"Order status updated to {order_status.value}"
        )
        await publish_order_event(
            event_type="order_status_changed",
            data=OrderEventData(
                order_id=order.id,
                order_num=order.order_no,
                user_id=order.user_id,
                status=order_status,
                status_message=status_message,
                payment_status=order.payment_status,
                total_amount=order.total,
            ),
        )

        loaded_order = await self.load_order(order.id)
        return loaded_order

    def _build_queries(
        self,
        order_status: OrderStatus | None = None,
        payment_status: PaymentStatus | None = None,
        payment_method: PaymentMethod | None = None,
    ):
        base_query = select(Order)

        count_query = select(func.count()).select_from(Order)

        filters = []

        if order_status is not None:
            filters.append(Order.order_status == order_status)

        if payment_status is not None:
            filters.append(Order.payment_status == payment_status)

        if payment_method is not None:
            filters.append(Order.payment_method == payment_method)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        return base_query, count_query

    async def get_order_stats(
        self,
        start_date: date,
        end_date: date,
    ):
        end_date = end_date + timedelta(days=1)

        result = await self.session.execute(
            select(func.count(Order.id)).where(
                Order.created_at >= start_date, Order.created_at < end_date
            )
        )

        total_orders = result.scalar() or 0

        result = await self.session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.created_at >= start_date, Order.created_at < end_date
            )
        )

        total_sales = result.scalar() or Decimal(0)

        return {
            "total_orders": total_orders,
            "total_sales": total_sales,
        }

    async def get_orders_by_status(
        self,
        start_date: date,
        end_date: date,
    ):
        end_date = end_date + timedelta(days=1)

        result = await self.session.execute(
            select(Order.order_status, func.count(Order.id))
            .where(Order.created_at >= start_date, Order.created_at < end_date)
            .group_by(Order.order_status)
        )

        return {status.value: count for status, count in result.all()}

    async def get_top_selling_pizzas(
        self,
        start_date: date,
        end_date: date,
        limit: int | None = None,
    ):
        end_date = end_date + timedelta(days=1)

        result = await self.session.execute(
            select(OrderItem.pizza_name, func.sum(OrderItem.quantity))
            .join(OrderItem.order)
            .where(Order.created_at >= start_date, Order.created_at < end_date)
            .group_by(OrderItem.pizza_name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(limit)
        )

        return [{"name": name, "sold": sold} for name, sold in result.all()]

    async def get_monthly_sales(self, months_count: int = 6):
        month_trunc = func.date_trunc("month", Order.created_at)

        stmt = (
            select(
                func.to_char(month_trunc, "YYYY-MM").label("month"),
                func.count(Order.id).label("total_orders"),
                func.sum(Order.total).label("revenue"),
            )
            .where(
                Order.created_at
                >= func.date_trunc("month", func.now())
                - text(f"INTERVAL '{months_count - 1} months'")
            )
            .group_by(month_trunc)
            .order_by(month_trunc)
        )

        result = await self.session.execute(stmt)

        return result.mappings().all()
