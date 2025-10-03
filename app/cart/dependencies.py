from fastapi import Depends, Request, Response
from typing import Annotated
from app.core.database import SessionDep
from app.auth.dependencies import OptionalUserDep
from app.cart.service import CartService
from app.cart.utils import get_cart_id_from_cookie, set_cart_cookie
from app.cart.model import Cart


async def get_or_create_cart(
    request: Request,
    response: Response,
    session: SessionDep,
    current_user: OptionalUserDep,
):
    service = CartService(session)
    if current_user:
        return await service.get_or_create_user_cart(user_id=current_user.id)

    cart_id = get_cart_id_from_cookie(request)
    cart = await service.get_or_create_guest_cart(cart_id)

    # set newly-created cart-cookie
    if not cart_id or str(cart_id) != str(cart.id):
        set_cart_cookie(response, cart.id)
    return cart


GetOrCreateCartDep = Annotated[Cart, Depends(get_or_create_cart)]
