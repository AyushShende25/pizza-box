from fastapi import APIRouter, Request, Response
from uuid import UUID
from app.core.database import SessionDep
from app.auth.dependencies import OptionalUserDep, CurrentUserDep
from app.cart.service import CartService
from app.cart.schema import (
    CartResponse,
    CartItemCreate,
    CartItemUpdate,
)
from app.cart.dependencies import GetOrCreateCartDep
from app.cart.utils import get_cart_id_from_cookie, clear_cart_cookie

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


@cart_router.get("/", response_model=CartResponse)
async def get_cart(cart: GetOrCreateCartDep):
    """Get current cart (guest or user)"""
    return cart


@cart_router.post("/items", response_model=CartResponse)
async def add_item_to_cart(
    item_data: CartItemCreate,
    request: Request,
    response: Response,
    session: SessionDep,
    current_user: OptionalUserDep,
    cart: GetOrCreateCartDep,
):
    """Add item to cart"""
    return await CartService(session=session).add_item_to_cart(
        cart_id=cart.id, item_data=item_data
    )


@cart_router.put("/items/{item_id}", response_model=CartResponse)
async def update_cart_item(
    item_id: UUID,
    update_data: CartItemUpdate,
    session: SessionDep,
):
    """Update cart item quantity"""
    return await CartService(session=session).update_cart_item(
        cart_item_id=item_id, update_data=update_data
    )


@cart_router.delete("/items/{item_id}")
async def remove_cart_item(
    item_id: UUID,
    session: SessionDep,
):
    """Remove item from cart"""
    await CartService(session=session).remove_cart_item(cart_item_id=item_id)
    return {"message": "Item removed from cart"}


@cart_router.delete("/")
async def clear_cart(
    request: Request,
    response: Response,
    current_user: OptionalUserDep,
    session: SessionDep,
    cart: GetOrCreateCartDep,
):
    """Clear all items from cart"""
    await CartService(session=session).clear_cart(cart_id=cart.id)

    return {"message": "Cart cleared successfully"}


@cart_router.post("/merge", response_model=CartResponse)
async def merge_guest_cart(
    request: Request,
    response: Response,
    session: SessionDep,
    current_user: CurrentUserDep,
):
    """
    Merge guest cart to user cart on login.
    This endpoint should be called after successful authentication.
    """
    guest_cart_id = get_cart_id_from_cookie(request)
    if guest_cart_id:
        user_cart = await CartService(session=session).merge_guest_cart_to_user(
            guest_cart_id, user_id=current_user.id
        )
        clear_cart_cookie(response)
        return user_cart
    else:
        # No guest cart, just return user's cart
        return await CartService(session=session).get_or_create_user_cart(
            user_id=current_user.id
        )
