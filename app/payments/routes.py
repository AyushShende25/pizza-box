import uuid

from fastapi import APIRouter, status

from app.payments.model import PaymentTransactionStatus
from app.payments.schema import VerifyPaymentCreate

from .dependencies import PaymentServiceDep

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


@payments_router.post(
    "/checkout/{order_id}",
    status_code=status.HTTP_200_OK,
)
async def checkout(
    payment_service: PaymentServiceDep,
    order_id: uuid.UUID,
):
    payment = await payment_service.create_razorpay_order(order_id)
    return {
        "success": True,
        "payment": {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "razorpay_order_id": payment.razorpay_order_id,
        },
    }


@payments_router.post(
    "/verify",
    status_code=status.HTTP_200_OK,
)
async def verify_payment(
    payment_service: PaymentServiceDep,
    data: VerifyPaymentCreate,
):
    payment = await payment_service.verify_payment(
        data.payment_id,
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature,
    )
    return {"success": payment.status == PaymentTransactionStatus.SUCCESS}
