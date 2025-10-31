import uuid
from app.address.model import Address


def generate_order_num() -> str:
    return f"PBX-{uuid.uuid4().hex[:8].upper()}"


def format_address(address: Address) -> str:
    return (
        f"{address.full_name}, {address.phone_number}, "
        f"{address.street}, {address.city}, {address.state}, "
        f"{address.postal_code}, {address.country}"
    )
