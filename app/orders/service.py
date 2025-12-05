from sqlalchemy.ext.asyncio import AsyncSession
from decimal import Decimal
from sqlalchemy import select, desc, and_, func, asc
from sqlalchemy.orm import selectinload
from datetime import datetime
import uuid
import asyncio
import math
import json
from app.orders.schema import OrderCreate
from app.orders.utils import generate_order_num, format_address
from app.menu.service import PizzaService, CrustService, SizeService
from app.menu.model import Topping
from app.orders.constants import TAX_RATE, DELIVERY_CHARGE
from app.orders.model import (
    Order,
    OrderItem,
    OrderItemTopping,
    OrderStatus,
    PaymentStatus,
    PaymentMethod,
)
from app.address.service import AddressesService
from app.core.exceptions import (
    OrderNotFoundError,
    OrderCancelFailure,
    ToppingNotFoundError,
    OrderStatusUpdateError,
)
from app.notifications.events import publish_order_event
from app.notifications.schema import OrderEventData

ORDER_STATUS_MESSAGES = {
    OrderStatus.CONFIRMED: "Restaurant has confirmed your order.",
    OrderStatus.PREPARING: "Your pizza is being prepared!",
    OrderStatus.OUT_FOR_DELIVERY: "Your order is on its way!",
    OrderStatus.DELIVERED: "Your order has been delivered!",
    OrderStatus.CANCELLED: "Your order has been cancelled.",
}


class OrderService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def load_order(self, order_id: uuid.UUID):
        return await self.session.scalar(
            select(Order)
            .options(selectinload(Order.order_items).selectinload(OrderItem.toppings))
            .where(Order.id == order_id)
        )

    async def create_order(self, data: OrderCreate, user_id: uuid.UUID):
        address = await AddressesService(self.session).get_one(data.address_id, user_id)

        payment_method = getattr(data, "payment_method", PaymentMethod.DIGITAL)

        order = Order(
            order_no=generate_order_num(),
            user_id=user_id,
            address_id=data.address_id,
            delivery_address=format_address(address),
            notes=data.notes,
            subtotal=Decimal("0.00"),
            tax=Decimal("0.00"),
            delivery_charge=DELIVERY_CHARGE,
            total=Decimal("0.00"),
            payment_method=payment_method,
        )

        subtotal = Decimal("0.00")

        pizza_service = PizzaService(self.session)
        size_service = SizeService(self.session)
        crust_service = CrustService(self.session)
        for order_item_data in data.order_items:
            pizza, size, crust = await asyncio.gather(
                pizza_service.get_one(order_item_data.pizza_id, load_toppings=False),
                size_service.get_one(order_item_data.size_id),
                crust_service.get_one(order_item_data.crust_id),
            )

            toppings: list[Topping] = []
            toppings_total = Decimal("0.00")

            if order_item_data.toppings_ids:
                toppings = list(
                    (
                        await self.session.scalars(
                            select(Topping).where(
                                Topping.id.in_(order_item_data.toppings_ids)
                            )
                        )
                    ).all()
                )
                if len(toppings) != len(order_item_data.toppings_ids):
                    found_ids = {t.id for t in toppings}
                    missing_ids = set(order_item_data.toppings_ids) - found_ids
                    raise ToppingNotFoundError(f"Toppings not found: {missing_ids}")

                toppings_total = sum((t.price for t in toppings), Decimal("0.00"))
            base_pizza_price = pizza.base_price
            size_price = size.multiplier * base_pizza_price
            crust_price = crust.additional_price
            unit_price = size_price + crust_price + toppings_total
            total_price = unit_price * order_item_data.quantity
            subtotal += total_price

            order_item = OrderItem(
                pizza_id=pizza.id,
                size_id=size.id,
                crust_id=crust.id,
                pizza_name=pizza.name,
                size_name=size.name,
                crust_name=crust.name,
                size_price=size_price,
                crust_price=crust_price,
                base_pizza_price=base_pizza_price,
                toppings_total_price=toppings_total,
                unit_price=unit_price,
                total_price=total_price,
                quantity=order_item_data.quantity,
            )

            for topping in toppings:
                order_item_topping = OrderItemTopping(
                    topping_id=topping.id,
                    topping_name=topping.name,
                    topping_price=topping.price,
                )
                order_item.toppings.append(order_item_topping)

            order.order_items.append(order_item)
        order.subtotal = subtotal
        order.tax = subtotal * TAX_RATE
        order.total = subtotal + order.tax + DELIVERY_CHARGE

        self.session.add(order)
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
        user_id: uuid.UUID,
        page: int = 1,
        limit: int = 10,
        order_status: OrderStatus | None = None,
        payment_status: PaymentStatus | None = None,
    ):
        skip = (page - 1) * limit
        base_query, _ = self._build_queries(order_status, payment_status)
        stmt = (
            base_query.options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .offset(skip)
        )
        result = await self.session.scalars(stmt)
        return result.all()

    async def get_user_order(
        self,
        user_id: uuid.UUID,
        order_id: uuid.UUID,
    ):
        order = await self.session.scalar(
            select(Order)
            .where(Order.id == order_id, Order.user_id == user_id)
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
        )
        if not order:
            raise OrderNotFoundError()
        return order

    async def get_order(
        self,
        order_id: uuid.UUID,
    ):
        order = await self.session.scalar(
            select(Order)
            .where(Order.id == order_id)
            .options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
        )
        if not order:
            raise OrderNotFoundError()
        return order

    async def cancel_user_order(self, user_id: uuid.UUID, order_id: uuid.UUID):
        order = await self.get_user_order(user_id, order_id)
        if order.order_status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise OrderCancelFailure(message="Cannot cancel order in current status")

        if order.payment_status == PaymentStatus.PAID:
            raise OrderCancelFailure(
                message="Cannot cancel paid order. Please request refund."
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
        page: int = 1,
        limit: int = 10,
        sort_by: str = "created_at:desc",
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

        field, order = self._parse_sort_params(sort_by)
        sort_column = getattr(Order, field, Order.created_at)
        sort_order = asc(sort_column) if order.lower() == "asc" else desc(sort_column)

        result = await self.session.scalars(
            base_query.options(
                selectinload(Order.order_items).selectinload(OrderItem.toppings),
            )
            .order_by(sort_order)
            .limit(limit)
            .offset(skip)
        )

        total = await self.session.scalar(count_query)

        return {
            "items": result.all(),
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total else 0,
        }

    async def update_order_status(self, order_id: uuid.UUID, order_status: OrderStatus):
        order = await self.session.scalar(select(Order).where(Order.id == order_id))
        if not order:
            raise OrderNotFoundError()

        valid_transitions = {
            OrderStatus.PENDING: [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
            OrderStatus.CONFIRMED: [OrderStatus.PREPARING, OrderStatus.CANCELLED],
            OrderStatus.PREPARING: [OrderStatus.OUT_FOR_DELIVERY],
            OrderStatus.OUT_FOR_DELIVERY: [OrderStatus.DELIVERED],
        }
        if order_status not in valid_transitions.get(order.order_status, []):
            raise OrderStatusUpdateError(
                f"Cannot transition from {order.order_status.value} to {order_status.value}"
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

    def _parse_sort_params(self, sort_by: str) -> tuple[str, str]:
        try:
            parts = sort_by.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid sort format")
            field, order = parts
            valid_fields = {
                "created_at",
                "order_no",
                "total",
            }
            field = field if field in valid_fields else "created_at"
            order = order if order.lower() in {"asc", "desc"} else "desc"

            return field, order
        except ValueError:
            return "created_at", "desc"
