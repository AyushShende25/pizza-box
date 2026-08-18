from typing import Annotated

from fastapi import Cookie, Depends, Response

from app.auth.dependencies import OptionalUserDep
from app.core.database import SessionDep

from .constants import CART_COOKIE_NAME
from .model import Cart
from .service import CartService
from .utils import get_cart_id_from_cookie, set_cart_cookie


def get_cart_service(session: SessionDep) -> CartService:
    """Provides a fresh CartService instance"""
    return CartService(session)


CartServiceDep = Annotated[CartService, Depends(get_cart_service)]


async def get_or_create_cart(
    response: Response,
    cart_service: CartServiceDep,
    current_user: OptionalUserDep,
    cart_id_cookie: Annotated[str | None, Cookie(alias=CART_COOKIE_NAME)] = None,
):
    if current_user:
        return await cart_service.get_or_create_user_cart(user_id=current_user.id)

    cart_id = get_cart_id_from_cookie(cookie=cart_id_cookie)
    cart = await cart_service.get_or_create_guest_cart(cart_id=cart_id)

    # set newly-created cart-cookie
    if not cart_id or str(cart_id) != str(cart.id):
        set_cart_cookie(response, cart.id)
    return cart


GetOrCreateCartDep = Annotated[Cart, Depends(get_or_create_cart)]
