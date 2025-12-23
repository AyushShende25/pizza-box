from fastapi import Request, Response
from uuid import UUID
from app.cart.constants import CART_COOKIE_NAME, CART_COOKIE_MAX_AGE
from app.core.config import settings


def get_cart_id_from_cookie(request: Request) -> UUID | None:
    """Extract cart_id from signed cookie"""
    cart_id_str = request.cookies.get(CART_COOKIE_NAME)
    if not cart_id_str:
        return None
    try:
        return UUID(cart_id_str)
    except ValueError:
        return None
    return None


def set_cart_cookie(response: Response, cart_id: UUID):
    """Set signed cart_id cookie"""
    response.set_cookie(
        key=CART_COOKIE_NAME,
        value=str(cart_id),
        max_age=CART_COOKIE_MAX_AGE,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
    )


def clear_cart_cookie(response: Response):
    """Clear cart_id cookie"""
    response.delete_cookie(key=CART_COOKIE_NAME)
