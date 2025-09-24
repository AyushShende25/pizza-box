from fastapi import APIRouter, Request, Response
from uuid import UUID
from app.core.database import SessionDep
from app.auth.dependencies import OptionalUserDep, CurrentUserDep
from app.cart.constants import CART_COOKIE_NAME, CART_COOKIE_MAX_AGE
from app.core.config import settings
from app.cart.service import CartService
from app.cart.schema import (
    CartResponse,
    CartItemResponse,
    CartItemCreate,
    CartItemUpdate,
)

cart_router = APIRouter(prefix="/cart", tags=["Cart"])


def get_cart_id_from_cookie(request: Request) -> UUID | None:
    """Extract cart_id from signed cookie"""
    cart_id_str = request.cookies.get(CART_COOKIE_NAME)
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
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )


def clear_cart_cookie(response: Response):
    """Clear cart_id cookie"""
    response.delete_cookie(key=CART_COOKIE_NAME)


@cart_router.get("/", response_model=CartResponse)
async def get_cart(
    request: Request,
    response: Response,
    session: SessionDep,
    current_user: OptionalUserDep,
):
    """Get current cart (guest or user)"""
    if current_user:
        cart = await CartService(session=session).get_or_create_user_cart(
            user_id=current_user.id
        )
    else:
        cart_id = get_cart_id_from_cookie(request)

        cart = await CartService(session=session).get_or_create_guest_cart(
            cart_id=cart_id
        )

        if not cart_id or str(cart_id) != str(cart.id):
            set_cart_cookie(response, cart_id=cart.id)

    return cart


@cart_router.post("/items", response_model=CartItemResponse)
async def add_item_to_cart(
    item_data: CartItemCreate,
    request: Request,
    response: Response,
    session: SessionDep,
    current_user: OptionalUserDep,
):
    """Add item to cart"""
    if current_user:
        cart = await CartService(session=session).get_or_create_user_cart(
            user_id=current_user.id
        )
    else:
        cart_id = get_cart_id_from_cookie(request)

        cart = await CartService(session=session).get_or_create_guest_cart(
            cart_id=cart_id
        )
        if not cart_id:
            set_cart_cookie(response, cart_id=cart.id)

    return await CartService(session=session).add_item_to_cart(
        cart_id=cart.id, item_data=item_data
    )


@cart_router.put("/items/{item_id}", response_model=CartItemResponse)
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
):
    """Clear all items from cart"""
    if current_user:
        cart = await CartService(session=session).get_or_create_user_cart(
            user_id=current_user.id
        )
    else:
        cart_id = get_cart_id_from_cookie(request)
        if not cart_id:
            return {"message": "No cart to clear"}
        cart = await CartService(session=session).get_or_create_guest_cart(cart_id)

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
