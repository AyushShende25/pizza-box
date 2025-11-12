from fastapi import APIRouter
import uuid
from app.payments.service import PaymentService
from app.core.database import SessionDep
from app.payments.schema import VerifyPaymentCreate
from app.payments.model import PaymentTransactionStatus

payments_router = APIRouter(prefix="/payments", tags=["Payments"])


@payments_router.post("/checkout/{order_id}")
async def checkout(
    session: SessionDep,
    order_id: uuid.UUID,
):
    payment = await PaymentService(session).create_razorpay_order(order_id)
    return {
        "success": True,
        "payment": {
            "id": payment.id,
            "amount": payment.meta_data.get("amount"),
            "currency": payment.meta_data.get("currency"),
            "razorpay_order_id": payment.meta_data.get("id"),
        },
    }


@payments_router.post("/verify")
async def verify_payment(
    session: SessionDep,
    data: VerifyPaymentCreate,
):
    payment = await PaymentService(session).verify_payment(
        data.payment_id,
        data.razorpay_order_id,
        data.razorpay_payment_id,
        data.razorpay_signature,
    )
    return {"success": payment.status == PaymentTransactionStatus.SUCCESS}
