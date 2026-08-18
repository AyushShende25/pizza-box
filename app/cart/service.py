from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.cart.model import Cart, CartItem
from app.cart.schema import CartItemCreate, CartItemUpdate
from app.core.exceptions import BadRequestError, EntityNotFoundError
from app.menu.model import Pizza, Topping
from app.menu.service import CrustService, PizzaService, SizeService
from app.store_config.service import StoreConfigService

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

    async def _load_cart(
        self,
        cart_id: UUID,
    ) -> Cart:
        """Always return a fully loaded cart with all relationships"""
        stmt = (
            select(Cart)
            .where(Cart.id == cart_id)
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

        result = await self.session.execute(stmt)
        cart = result.scalar_one_or_none()

        if cart is None:
            raise EntityNotFoundError(
                error_code="CART_NOT_FOUND",
                message="Cart does not exist",
            )

        return cart

    async def get_guest_cart(
        self,
        guest_cart_id: UUID,
    ) -> Cart | None:
        """Get guest cart"""
        stmt = (
            select(Cart)
            .where(Cart.id == guest_cart_id, Cart.user_id.is_(None))
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_or_create_guest_cart(
        self,
        cart_id: UUID | None = None,
    ) -> Cart:
        """Get existing guest cart or create a new one"""
        if cart_id:
            cart = await self.get_guest_cart(guest_cart_id=cart_id)
            if cart:
                return cart

        cart = Cart(user_id=None)

        self.session.add(cart)
        await self.session.commit()

        return await self._load_cart(cart_id=cart.id)

    async def get_user_cart(self, user_id: UUID) -> Cart | None:
        """Get user's persistent cart"""
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(selectinload(Cart.cart_items).options(*CART_ITEM_OPTIONS))
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def get_or_create_user_cart(self, user_id: UUID) -> Cart:
        """Get existing user cart or create a new one"""
        cart = await self.get_user_cart(user_id)
        if cart:
            return cart

        cart = Cart(user_id=user_id)

        self.session.add(cart)
        await self.session.commit()

        return await self._load_cart(cart_id=cart.id)

    async def merge_guest_cart_to_user(
        self,
        guest_cart_id: UUID,
        user_id: UUID,
    ) -> Cart:
        """Merge guest cart into user cart when user logs in"""
        # Get guest cart (which has the given cart-id and user-id is null)
        guest_cart = await self.get_guest_cart(guest_cart_id=guest_cart_id)

        if not guest_cart:
            # No guest cart exists, just return or create user cart
            return await self.get_or_create_user_cart(user_id=user_id)

        # Guest-cart exists, check for user-cart
        user_cart = await self.get_user_cart(user_id=user_id)

        if not user_cart:
            # No existing user cart, just assign guest cart to user
            guest_cart.user_id = user_id
            await self.session.commit()
            return await self._load_cart(cart_id=guest_cart.id)

        # Both guest-cart and user-cart exists, Loop over guest-cart-items and merge them (if already exists) or insert them into user cart
        for guest_item in guest_cart.cart_items:
            existing_item = await self._find_matching_cart_item(
                cart=user_cart,
                item=guest_item,
            )

            if existing_item:
                # Increment quantity
                existing_item.quantity += guest_item.quantity
                existing_item.total = self._calculate_item_total(item=existing_item)
            else:
                # Copy guest item to user cart
                new_item = CartItem(
                    cart_id=user_cart.id,
                    pizza_id=guest_item.pizza_id,
                    size_id=guest_item.size_id,
                    crust_id=guest_item.crust_id,
                    quantity=guest_item.quantity,
                    total=guest_item.total,
                    toppings=guest_item.toppings,
                )

                self.session.add(new_item)

        # Delete guest cart - cascade will handle guest_cart_items automatically!
        await self.session.delete(guest_cart)

        await self._recalculate_cart_totals(cart=user_cart)

        await self.session.commit()

        return await self._load_cart(cart_id=user_cart.id)

    async def _find_matching_cart_item(
        self,
        cart: Cart,
        item: CartItem,
    ) -> CartItem | None:
        """Find cart item with same pizza configuration"""
        for cart_item in cart.cart_items:
            if (
                cart_item.pizza_id == item.pizza_id
                and cart_item.size_id == item.size_id
                and cart_item.crust_id == item.crust_id
            ):
                cart_item_toppings = {t.id for t in cart_item.toppings}

                item_toppings = {t.id for t in item.toppings}

                if cart_item_toppings == item_toppings:
                    return cart_item
        return None

    async def add_item_to_cart(self, cart_id: UUID, data: CartItemCreate):
        """Add item to cart"""
        cart = await self._load_cart(cart_id)

        pizza = await PizzaService(self.session).get_one(data.pizza_id)

        size = await SizeService(self.session).get_one(data.size_id)

        crust = await CrustService(self.session).get_one(data.crust_id)

        if not pizza.is_available or not size.is_available or not crust.is_available:
            raise BadRequestError(
                error_code="ITEM_UNAVAILABLE",
                message="One or more selected items are unavailable",
            )

        # Check if identical item already exists, if yes then simply increase the quantity and recalculate the totals
        existing_item = await self._find_existing_item(
            cart=cart,
            data=data,
        )

        if existing_item:
            existing_item.quantity += data.quantity

            existing_item.total = self._calculate_item_total(item=existing_item)

            await self._recalculate_cart_totals(cart=cart)

            await self.session.commit()

            return await self._load_cart(cart_id=cart.id)

        # CartItem does not exist so create a new one
        cart_item = CartItem(
            cart_id=cart_id,
            pizza=pizza,
            size=size,
            crust=crust,
            quantity=data.quantity,
            total=Decimal(0),
        )

        # Add toppings if specified
        if data.topping_ids:
            stmt = select(Topping).where(Topping.id.in_(data.topping_ids))

            result = await self.session.execute(stmt)

            toppings = list(result.scalars().all())

            if len(toppings) != len(data.topping_ids):
                raise EntityNotFoundError(
                    error_code="TOPPING_NOT_FOUND",
                    message="One or more topping not found",
                )

            if any(not topping.is_available for topping in toppings):
                raise BadRequestError(
                    error_code="TOPPING_UNAVAILABLE",
                    message="One or more selected toppings are unavailable",
                )

            cart_item.toppings = toppings

        cart_item.total = self._calculate_item_total(item=cart_item)

        self.session.add(cart_item)

        await self._recalculate_cart_totals(cart=cart)

        await self.session.commit()

        return await self._load_cart(cart_id=cart.id)

    async def _find_existing_item(
        self,
        cart: Cart,
        data: CartItemCreate,
    ) -> CartItem | None:
        """Find existing cart item with same configuration"""
        topping_ids = set(data.topping_ids or [])

        for cart_item in cart.cart_items:
            if (
                cart_item.pizza_id == data.pizza_id
                and cart_item.crust_id == data.crust_id
                and cart_item.size_id == data.size_id
            ):
                item_topping_ids = {t.id for t in cart_item.toppings}

                if topping_ids == item_topping_ids:
                    return cart_item
        return None

    async def update_cart_item(
        self,
        cart_id: UUID,
        cart_item_id: UUID,
        data: CartItemUpdate,
    ) -> Cart:
        """Update cart item quantity"""
        result = await self.session.execute(
            select(CartItem)
            .where(
                CartItem.id == cart_item_id,
                CartItem.cart_id == cart_id,
            )
            .options(
                selectinload(CartItem.cart)
                .selectinload(Cart.cart_items)
                .options(*CART_ITEM_OPTIONS)
            )
        )

        cart_item = result.scalar_one_or_none()

        if not cart_item:
            raise EntityNotFoundError(
                error_code="CART_ITEM_NOT_FOUND",
                message="Cart item does not exist",
            )

        cart_item.quantity = data.quantity

        cart_item.total = self._calculate_item_total(item=cart_item)

        await self._recalculate_cart_totals(cart_item.cart)

        await self.session.commit()

        return await self._load_cart(cart_id=cart_item.cart_id)

    async def remove_cart_item(
        self,
        cart_id: UUID,
        cart_item_id: UUID,
    ):
        """Remove item from cart"""
        result = await self.session.execute(
            select(CartItem)
            .where(CartItem.id == cart_item_id, CartItem.cart_id == cart_id)
            .options(
                selectinload(CartItem.cart)
                .selectinload(Cart.cart_items)
                .options(*CART_ITEM_OPTIONS)
            )
        )

        cart_item = result.scalar_one_or_none()

        if not cart_item:
            raise EntityNotFoundError(
                error_code="CART_ITEM_NOT_FOUND",
                message="Cart item does not exist",
            )

        await self.session.delete(cart_item)

        await self._recalculate_cart_totals(cart=cart_item.cart)

        await self.session.commit()

        return await self._load_cart(cart_id=cart_item.cart_id)

    async def clear_cart(
        self,
        cart_id: UUID,
    ):
        """Clear all items from cart"""
        stmt = select(Cart).where(Cart.id == cart_id)

        result = await self.session.execute(stmt)

        cart = result.scalar_one_or_none()

        if not cart:
            raise EntityNotFoundError(
                error_code="CART_NOT_FOUND",
                message="Cart does not exist",
            )

        await self.session.execute(delete(CartItem).where(CartItem.cart_id == cart_id))

        cart.subtotal = Decimal(0)
        cart.tax = Decimal(0)
        cart.delivery_charge = Decimal(0)
        cart.total = Decimal(0)

        await self.session.commit()

        return await self._load_cart(cart_id=cart_id)

    def _calculate_item_total(
        self,
        item: CartItem,
    ) -> Decimal:
        base_price = item.pizza.base_price

        crust_price = item.crust.price_modifier

        size_price = item.size.price_modifier

        toppings_price = sum(
            (t.price_modifier for t in item.toppings),
            Decimal("0.00"),
        )

        return (base_price + size_price + crust_price + toppings_price) * item.quantity

    async def _recalculate_cart_totals(
        self,
        cart: Cart,
    ) -> Cart:
        """Recalculate cart totals"""
        store_config = await StoreConfigService(session=self.session).get()

        result = await self.session.execute(
            select(func.sum(CartItem.total)).where(CartItem.cart_id == cart.id)
        )

        subtotal = result.scalar() or Decimal(0)

        cart.subtotal = subtotal

        cart.tax = subtotal * store_config.tax_rate

        cart.delivery_charge = store_config.base_delivery_fee

        cart.total = cart.subtotal + cart.tax + cart.delivery_charge

        return cart
