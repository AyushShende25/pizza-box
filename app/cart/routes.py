from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Cookie, Response, status

from app.auth.dependencies import CurrentUserDep

from .constants import CART_COOKIE_NAME
from .dependencies import CartServiceDep, GetOrCreateCartDep
from .schema import (
    CartItemCreate,
    CartItemUpdate,
    CartResponse,
)
from .utils import clear_cart_cookie, get_cart_id_from_cookie

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=CartResponse,
)
async def get_cart(cart: GetOrCreateCartDep):
    """Get current cart (guest or user)"""
    return cart


@cart_router.post(
    "/items",
    status_code=status.HTTP_200_OK,
    response_model=CartResponse,
)
async def add_item_to_cart(
    data: CartItemCreate,
    cart_service: CartServiceDep,
    cart: GetOrCreateCartDep,
):
    """Add item to cart"""
    return await cart_service.add_item_to_cart(
        cart_id=cart.id,
        data=data,
    )


@cart_router.put(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
    response_model=CartResponse,
)
async def update_cart_item(
    item_id: UUID,
    data: CartItemUpdate,
    cart: GetOrCreateCartDep,
    cart_service: CartServiceDep,
):
    """Update cart item quantity"""
    return await cart_service.update_cart_item(
        cart_id=cart.id,
        cart_item_id=item_id,
        data=data,
    )


@cart_router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_200_OK,
)
async def remove_cart_item(
    item_id: UUID,
    cart: GetOrCreateCartDep,
    cart_service: CartServiceDep,
):
    """Remove item from cart"""
    await cart_service.remove_cart_item(
        cart_id=cart.id,
        cart_item_id=item_id,
    )
    return {"message": "Item removed from cart"}


@cart_router.delete(
    "/",
    status_code=status.HTTP_200_OK,
)
async def clear_cart(
    cart_service: CartServiceDep,
    cart: GetOrCreateCartDep,
):
    """Clear all items from cart"""
    await cart_service.clear_cart(cart_id=cart.id)

    return {"message": "Cart cleared successfully"}


@cart_router.post(
    "/merge",
    status_code=status.HTTP_200_OK,
    response_model=CartResponse,
)
async def merge_guest_cart(
    response: Response,
    cart_service: CartServiceDep,
    current_user: CurrentUserDep,
    cart_id_cookie: Annotated[str | None, Cookie(alias=CART_COOKIE_NAME)] = None,
):
    """
    Merge guest cart to user cart on login.
    This endpoint should be called after successful authentication.
    """
    guest_cart_id = get_cart_id_from_cookie(cookie=cart_id_cookie)

    if guest_cart_id:
        user_cart = await cart_service.merge_guest_cart_to_user(
            guest_cart_id=guest_cart_id,
            user_id=current_user.id,
        )

        clear_cart_cookie(response)

        return user_cart
    else:
        # No guest cart, just return user's cart
        return await cart_service.get_or_create_user_cart(user_id=current_user.id)
