from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import razorpay
from razorpay.errors import SignatureVerificationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException, BadRequestError, EntityNotFoundError
from app.notifications.events import publish_payment_event
from app.notifications.schema import PaymentEventData
from app.orders.model import Order, OrderStatus, PaymentMethod, PaymentStatus
from app.utils.logger import logger

from .model import Payment, PaymentProvider, PaymentTransactionStatus


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
        razorpay_client: razorpay.Client,
    ):
        self.session = session
        self.razorpay_client = razorpay_client

    async def create_razorpay_order(self, order_id: UUID) -> Payment:
        result = await self.session.execute(select(Order).where(Order.id == order_id))

        order = result.scalar_one_or_none()

        if not order:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Order with that id does not exist",
            )

        if order.payment_method != PaymentMethod.DIGITAL:
            raise BadRequestError(
                error_code="INVALID_PAYMENT_METHOD",
                message="Razorpay payment is only available for digital orders",
            )

        if order.order_status == OrderStatus.CANCELLED:
            raise BadRequestError(
                error_code="ORDER_CANCELLED",
                message="Cannot create payment for a cancelled order",
            )

        if order.payment_status == PaymentStatus.PAID:
            raise BadRequestError(
                error_code="ORDER_ALREADY_PAID",
                message="Order is already paid",
            )

        amount_in_paise = int(order.total * 100)

        payload = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order.order_no,
            "notes": {
                "order_id": str(order.id),
                "order_no": order.order_no,
            },
        }

        try:
            razorpay_order = self.razorpay_client.order.create(data=payload)
        except razorpay.errors.RazorpayError as exc:
            logger.exception(f"Razorpay order creation failed: {exc}")
            raise AppException(
                error_code="PAYMENT_GATEWAY_ERROR",
                message="Failed to initiate transaction with payment provider",
            )

        payment = Payment(
            order_id=order.id,
            user_id=order.user_id,
            provider=PaymentProvider.RAZORPAY,
            status=PaymentTransactionStatus.INITIATED,
            razorpay_order_id=razorpay_order["id"],
            amount=order.total,
            currency="INR",
            meta_data=razorpay_order,
        )

        self.session.add(payment)
        await self.session.commit()
        await self.session.refresh(payment)

        return payment

    async def _publish_payment_event_safely(
        self,
        event_type: str,
        user_id: UUID | None,
        order_num: str,
        amount: Decimal,
        status: PaymentTransactionStatus,
        provider: PaymentProvider,
        reason: str | None = None,
    ) -> None:
        if not user_id:
            logger.warning("Skipping event publishing: no user_id present")
            return

        try:
            await publish_payment_event(
                event_type=event_type,
                data=PaymentEventData(
                    user_id=user_id,
                    order_num=order_num,
                    amount=amount,
                    payment_status=status,
                    provider=provider,
                    reason=reason,
                ),
            )
        except Exception:
            logger.exception(f"Failed to publish payment event {event_type}")

    async def verify_payment(
        self,
        payment_id: UUID,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> Payment:
        result = await self.session.execute(
            select(Payment)
            .options(selectinload(Payment.order))
            .where(Payment.id == payment_id)
            .with_for_update()
        )
        payment = result.scalar_one_or_none()

        if not payment:
            raise EntityNotFoundError(
                error_code="PAYMENT_NOT_FOUND",
                message="Payment not found",
            )

        if payment.status == PaymentTransactionStatus.SUCCESS:
            return payment

        order = payment.order

        if not order:
            raise EntityNotFoundError(
                error_code="ORDER_NOT_FOUND",
                message="Associated order does not exist",
            )

        if order.payment_method != PaymentMethod.DIGITAL:
            raise BadRequestError(
                error_code="INVALID_PAYMENT_METHOD",
                message="This order does not use digital payment",
            )

        if order.payment_status == PaymentStatus.PAID:
            raise AppException(
                error_code="ORDER_ALREADY_PAID",
                message="Order has already been paid",
            )

        if payment.razorpay_order_id != razorpay_order_id:
            raise AppException(
                error_code="PAYMENT_ORDER_MISMATCH",
                message="Razorpay order does not match payment record",
            )

        try:
            self.razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
        except SignatureVerificationError:
            payment.status = PaymentTransactionStatus.FAILED
            payment.error_message = "Invalid payment signature"
            order.payment_status = PaymentStatus.FAILED
            await self.session.commit()

            await self._publish_payment_event_safely(
                event_type="payment_failed",
                user_id=payment.user_id,
                order_num=order.order_no,
                amount=payment.amount,
                status=payment.status,
                provider=payment.provider,
                reason=payment.error_message,
            )
            return payment

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = PaymentTransactionStatus.SUCCESS
        payment.completed_at = datetime.now(UTC)

        try:
            razorpay_payment_data = self.razorpay_client.payment.fetch(
                razorpay_payment_id
            )
            payment.meta_data = razorpay_payment_data
        except Exception:
            logger.warning(
                f"Failed to fetch Razorpay payment details for payment_id={payment.id}",
                exc_info=True,
            )

        order.payment_status = PaymentStatus.PAID
        order.order_status = OrderStatus.CONFIRMED

        await self.session.commit()
        await self.session.refresh(payment)

        await self._publish_payment_event_safely(
            event_type="payment_successful",
            user_id=payment.user_id,
            order_num=order.order_no,
            amount=payment.amount,
            status=payment.status,
            provider=payment.provider,
        )

        return payment
