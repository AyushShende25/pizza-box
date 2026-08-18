from uuid import UUID

from fastapi import Response

from app.cart.constants import CART_COOKIE_MAX_AGE, CART_COOKIE_NAME
from app.core.config import settings


def get_cart_id_from_cookie(cookie: str | None) -> UUID | None:
    """Extract cart ID from cookie."""
    if not cookie:
        return None
    try:
        return UUID(cookie)
    except ValueError:
        return None


def set_cart_cookie(response: Response, cart_id: UUID):
    """Set cart_id cookie"""
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
