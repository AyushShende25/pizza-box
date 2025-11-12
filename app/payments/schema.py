import uuid
from app.core.base_schema import BaseSchema


class VerifyPaymentCreate(BaseSchema):
    payment_id: uuid.UUID
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
