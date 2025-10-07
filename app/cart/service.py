from app.core.database import AsyncSession
from app.cart.schema import CartItemCreate, CartItemUpdate
from app.cart.model import Cart, CartItem
from app.menu.service import PizzaService, SizeService, CrustService
from sqlalchemy import select, delete, func
from sqlalchemy.orm import selectinload
from app.menu.model import Topping
from uuid import UUID
from app.core.exceptions import (
    CartNotFoundError,
    ToppingNotFoundError,
    CartItemNotFoundError,
)
from app.cart.constants import TAX_RATE, DELIVERY_CHARGE
from app.menu.model import Pizza
from decimal import Decimal
import asyncio

CART_ITEM_OPTIONS = (
    selectinload(CartItem.pizza).selectinload(Pizza.default_toppings),
    selectinload(CartItem.size),
    selectinload(CartItem.crust),
    selectinload(CartItem.toppings),
)


class CartService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def _load_cart(self, cart_id: UUID):
        """Always return a fully loaded cart with all relationships"""
        return await self.session.scalar(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

    async def get_guest_cart(self, guest_cart_id: UUID) -> Cart | None:
        """Get guest cart"""
        return await self.session.scalar(
            select(Cart)
            .where(Cart.id == guest_cart_id, Cart.user_id.is_(None))
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

    async def get_or_create_guest_cart(self, cart_id: UUID | None = None) -> Cart:
        """Get existing guest cart or create a new one"""
        if cart_id:
            cart = await self.get_guest_cart(cart_id)
            if cart:
                return cart
        cart = Cart(user_id=None)
        self.session.add(cart)
        await self.session.commit()
        return await self._load_cart(cart.id)

    async def get_user_cart(self, user_id: UUID) -> Cart | None:
        """Get user's persistent cart"""
        return await self.session.scalar(
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

    async def get_or_create_user_cart(self, user_id: UUID) -> Cart:
        """Get existing user cart or create a new one"""
        cart = await self.get_user_cart(user_id)
        if cart:
            return cart
        cart = Cart(user_id=user_id)
        self.session.add(cart)
        await self.session.commit()
        return await self._load_cart(cart.id)

    async def merge_guest_cart_to_user(
        self, guest_cart_id: UUID, user_id: UUID
    ) -> Cart:
        """Merge guest cart into user cart when user logs in"""
        # Get guest cart (which has the given cart-id and user-id is null)
        guest_cart = await self.get_guest_cart(guest_cart_id)

        if not guest_cart:
            # No guest cart exists, just return or create user cart
            return await self.get_or_create_user_cart(user_id)

        # Guest-cart exists, check for user-cart
        user_cart = await self.get_user_cart(user_id)

        if not user_cart:
            # No existing user cart, just assign guest cart to user
            guest_cart.user_id = user_id
            await self.session.commit()
            return await self._load_cart(guest_cart.id)

        # Both guest-cart and user-cart exists, Loop over guest-cart-items and merge them (if already exists) or insert them into user cart
        for guest_item in guest_cart.cart_items:
            existing_item = await self._find_matching_cart_item(user_cart, guest_item)

            if existing_item:
                # Increment quantity
                existing_item.quantity += guest_item.quantity
                existing_item.total = self._calculate_item_total(existing_item)
            else:
                # Move guest item to user cart
                guest_item.cart_id = user_cart.id

        # Delete guest cart - cascade will handle guest_cart_items automatically!
        await self.session.delete(guest_cart)
        await self._recalculate_cart_totals(user_cart)
        await self.session.commit()
        return await self._load_cart(user_cart.id)

    async def _find_matching_cart_item(
        self, cart: Cart, item: CartItem
    ) -> CartItem | None:
        """Find cart item with same pizza configuration"""
        for cart_item in cart.cart_items:
            if (
                cart_item.pizza_id == item.pizza_id
                and cart_item.size_id == item.size_id
                and cart_item.crust_id == item.crust_id
            ):
                cart_item_toppings = set(t.id for t in cart_item.toppings)
                item_toppings = set(t.id for t in item.toppings)

                if cart_item_toppings == item_toppings:
                    return cart_item

        return None

    async def add_item_to_cart(self, cart_id: UUID, item_data: CartItemCreate):
        """Add item to cart"""
        cart = await self._load_cart(cart_id)
        if not cart:
            raise CartNotFoundError()

        pizza, size, crust = await asyncio.gather(
            PizzaService(self.session).get_one(item_data.pizza_id),
            SizeService(self.session).get_one(item_data.size_id),
            CrustService(self.session).get_one(item_data.crust_id),
        )

        # Check if identical item already exists, if yes then simply increase the quantity and recalculate the totals
        existing_item = await self._find_existing_item(cart, item_data)

        if existing_item:
            existing_item.quantity += item_data.quantity
            existing_item.total = self._calculate_item_total(existing_item)
            await self._recalculate_cart_totals(cart)
            await self.session.commit()
            return await self._load_cart(cart.id)

        # CartItem does not exist so create a new one
        cart_item = CartItem(
            cart_id=cart_id,
            pizza=pizza,
            size=size,
            crust=crust,
            quantity=item_data.quantity,
            total=Decimal("0"),
        )

        # Add toppings if specified
        if item_data.topping_ids:
            toppings = list(
                await self.session.scalars(
                    select(Topping).where(Topping.id.in_(item_data.topping_ids))
                )
            )
            if len(toppings) != len(item_data.topping_ids):
                raise ToppingNotFoundError(message="One or more toppings not found")
            cart_item.toppings = toppings

        cart_item.total = self._calculate_item_total(cart_item)
        self.session.add(cart_item)
        await self._recalculate_cart_totals(cart)
        await self.session.commit()
        return await self._load_cart(cart.id)

    async def _find_existing_item(
        self, cart: Cart, item_data: CartItemCreate
    ) -> CartItem | None:
        """Find existing cart item with same configuration"""
        topping_ids = set(item_data.topping_ids or [])

        for cart_item in cart.cart_items:
            if (
                cart_item.pizza_id == item_data.pizza_id
                and cart_item.crust_id == item_data.crust_id
                and cart_item.size_id == item_data.size_id
            ):
                item_topping_ids = set(t.id for t in cart_item.toppings)
                if topping_ids == item_topping_ids:
                    return cart_item
        return None

    async def update_cart_item(
        self, cart_item_id: UUID, update_data: CartItemUpdate
    ) -> Cart:
        """Update cart item quantity"""
        cart_item = await self.session.scalar(
            select(CartItem)
            .where(CartItem.id == cart_item_id)
            .options(
                selectinload(CartItem.cart)
                .selectinload(Cart.cart_items)
                .options(*CART_ITEM_OPTIONS)
            )
        )
        if not cart_item:
            raise CartItemNotFoundError()

        cart_item.quantity = update_data.quantity
        cart_item.total = self._calculate_item_total(cart_item)

        await self._recalculate_cart_totals(cart_item.cart)
        await self.session.commit()
        return await self._load_cart(cart_item.cart_id)

    async def remove_cart_item(self, cart_item_id: UUID):
        """Remove item from cart"""
        cart_item = await self.session.scalar(
            select(CartItem)
            .where(CartItem.id == cart_item_id)
            .options(
                selectinload(CartItem.cart)
                .selectinload(Cart.cart_items)
                .options(*CART_ITEM_OPTIONS)
            )
        )
        if not cart_item:
            raise CartItemNotFoundError()

        await self.session.delete(cart_item)
        await self._recalculate_cart_totals(cart_item.cart)
        await self.session.commit()
        return await self._load_cart(cart_item.cart_id)

    async def clear_cart(self, cart_id: UUID):
        """Clear all items from cart"""
        cart = await self.session.get(Cart, cart_id)
        if not cart:
            raise CartNotFoundError()

        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))

        cart.subtotal = Decimal("0")
        cart.tax = Decimal("0")
        cart.delivery_charge = Decimal("0")
        cart.total = Decimal("0")

        await self.session.commit()
        return await self._load_cart(cart_id)

    def _calculate_item_total(self, item: CartItem) -> Decimal:
        base_price = Decimal(item.pizza.base_price)
        crust_price = Decimal(item.crust.additional_price)
        toppings_price = sum(Decimal(t.price) for t in item.toppings)
        size_price = base_price * Decimal(item.size.multiplier)
        return (size_price + crust_price + toppings_price) * item.quantity

    async def _recalculate_cart_totals(self, cart: Cart):
        """Recalculate cart totals"""
        result = await self.session.execute(
            select(func.sum(CartItem.total)).where(CartItem.cart_id == cart.id)
        )
        subtotal = result.scalar() or Decimal("0")
        cart.subtotal = Decimal(subtotal)
        cart.tax = subtotal * Decimal(TAX_RATE)
        cart.delivery_charge = (
            Decimal(DELIVERY_CHARGE) if subtotal > Decimal("0") else Decimal("0")
        )
        cart.total = subtotal + cart.tax + cart.delivery_charge
        return cart
