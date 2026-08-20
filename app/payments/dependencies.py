from typing import Annotated

from fastapi import Depends

from app.core.database import SessionDep
from app.libs.razorpay import razorpay_client

from .service import PaymentService


def get_payment_service(session: SessionDep) -> PaymentService:
    """Provides a fresh PaymentService instance"""
    return PaymentService(session=session, razorpay_client=razorpay_client)


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]
