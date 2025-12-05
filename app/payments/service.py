from sqlalchemy.ext.asyncio import AsyncSession
from razorpay.errors import SignatureVerificationError
from sqlalchemy import select, func
import uuid
from app.libs.razorpay import razorpay_client
from app.orders.model import Order
from app.core.exceptions import (
    OrderNotFoundError,
    PaymentCreationError,
    PaymentNotFoundError,
)
from app.payments.model import Payment, PaymentProvider, PaymentTransactionStatus
from app.orders.model import OrderStatus, PaymentStatus
from app.notifications.events import publish_payment_event
from app.notifications.schema import PaymentEventData
from app.utils.logger import logger


class PaymentService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.razorpay_client = razorpay_client

    async def create_razorpay_order(self, order_id: uuid.UUID):
        order = await self.session.scalar(select(Order).where(Order.id == order_id))
        if not order:
            raise OrderNotFoundError()

        amount_in_paise = int(order.total * 100)
        try:
            razorpay_order = self.razorpay_client.order.create(
                data={
                    "amount": amount_in_paise,
                    "currency": "INR",
                    "receipt": order.order_no,
                    "notes": {
                        "order_id": str(order.id),
                        "order_no": order.order_no,
                    },
                }
            )
        except Exception as e:
            raise PaymentCreationError(f"Razorpay order creation failed: {str(e)}")

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

    async def verify_payment(
        self,
        payment_id: uuid.UUID,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ):
        payment = await self.session.scalar(
            select(Payment).where(Payment.id == payment_id)
        )
        if not payment:
            raise PaymentNotFoundError()

        if payment.status == PaymentTransactionStatus.SUCCESS:
            return payment

        try:
            self.razorpay_client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": razorpay_order_id,
                    "razorpay_payment_id": razorpay_payment_id,
                    "razorpay_signature": razorpay_signature,
                }
            )
        except SignatureVerificationError:
            payment.status = PaymentTransactionStatus.FAILED
            payment.error_message = "Invalid payment signature"
            await self.session.commit()

            # This is very unlikely to happen, added just for type-check satisfaction
            if not payment.user_id:
                logger.warning(
                    f"Skipping notification for payment {payment.id} — no user_id"
                )
                return payment
            await publish_payment_event(
                event_type="payment_failed",
                data=PaymentEventData(
                    user_id=payment.user_id,
                    order_num=payment.order.order_no,
                    payment_status=payment.status,
                    provider=payment.provider,
                    amount=payment.amount,
                    reason="Invalid payment signature",
                ),
            )

            return payment
        except Exception as e:
            payment.status = PaymentTransactionStatus.FAILED
            payment.error_message = f"Verification error: {str(e)}"
            await self.session.commit()

            # This is very unlikely to happen, added just type-check satisfaction
            if not payment.user_id:
                logger.warning(
                    f"Skipping notification for payment {payment.id} — no user_id"
                )
                return payment
            await publish_payment_event(
                event_type="payment_failed",
                data=PaymentEventData(
                    user_id=payment.user_id,
                    order_num=payment.order.order_no,
                    payment_status=payment.status,
                    provider=payment.provider,
                    amount=payment.amount,
                    reason=str(e),
                ),
            )

            raise PaymentCreationError(f"Payment verification failed: {str(e)}")

        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = PaymentTransactionStatus.SUCCESS
        payment.completed_at = func.now()
        try:
            razorpay_payment_data = self.razorpay_client.payment.fetch(
                razorpay_payment_id
            )
            payment.meta_data = razorpay_payment_data
        except Exception:
            pass

        order = await self.session.scalar(
            select(Order).where(Order.id == payment.order_id)
        )
        if not order:
            raise OrderNotFoundError()
        order.payment_status = PaymentStatus.PAID
        order.order_status = OrderStatus.CONFIRMED

        await self.session.commit()
        await self.session.refresh(payment)

        # This is very unlikely to happen, added just type-check satisfaction
        if not payment.user_id:
            logger.warning(
                f"Skipping notification for payment {payment.id} — no user_id"
            )
            return payment
        await publish_payment_event(
            event_type="payment_successful",
            data=PaymentEventData(
                user_id=payment.user_id,
                order_num=payment.order.order_no,
                amount=payment.amount,
                payment_status=payment.status,
                provider=payment.provider,
            ),
        )

        return payment
