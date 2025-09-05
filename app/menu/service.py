from sqlalchemy import select, asc, desc, func, and_
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.menu.model import Pizza, Topping, ToppingCategory, Size, Crust, PizzaCategory
from app.menu.schema import (
    PizzaCreate,
    PizzaUpdate,
    ToppingCreate,
    ToppingUpdate,
    SizeCreate,
    SizeUpdate,
    CrustCreate,
    CrustUpdate,
)
from app.core.database import AsyncSession
from app.core.exceptions import (
    PizzaAlreadyExistsError,
    PizzaNotFoundError,
    ToppingAlreadyExistsError,
    ToppingNotFoundError,
    SizeAlreadyExistsError,
    SizeNotFoundError,
    CrustAlreadyExistsError,
    CrustNotFoundError,
)
import math


class PizzaService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(
        self,
        page: int = 1,
        limit: int = 5,
        sort_by: str = "created_at:asc",
        category: PizzaCategory | None = None,
        name: str | None = None,
        is_available: bool | None = None,
    ):
        skip = (page - 1) * limit

        field, order = self._parse_sort_params(sort_by)
        sort_column = getattr(Pizza, field, Pizza.created_at)
        sort_order = asc(sort_column) if order.lower() == "asc" else desc(sort_column)

        base_query, count_query = self._build_queries(category, name, is_available)

        total = await self.session.scalar(count_query)

        stmt = base_query.order_by(sort_order).limit(limit).offset(skip)

        result = await self.session.scalars(stmt)
        return {
            "items": result.all(),
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total else 0,
        }

    def _parse_sort_params(self, sort_by: str) -> tuple[str, str]:
        try:
            parts = sort_by.split(":")
            if len(parts) != 2:
                raise ValueError("Invalid sort format")
            field, order = parts
            valid_fields = {
                "created_at",
                "updated_at",
                "name",
                "base_price",
                "category",
            }
            if field not in valid_fields:
                field = "created_at"

            if order.lower() not in {"asc", "desc"}:
                order = "desc"

            return field, order
        except ValueError:
            return "created_at", "desc"

    def _build_queries(
        self,
        category: PizzaCategory | None,
        name: str | None,
        is_available: bool | None,
    ):
        base_query = select(Pizza).options(selectinload(Pizza.default_toppings))
        count_query = select(func.count()).select_from(Pizza)

        filters = []

        if category:
            filters.append(Pizza.category == category)

        if name:
            filters.append(Pizza.name.ilike(f"%{name}%"))

        if is_available is not None:
            filters.append(Pizza.is_available == is_available)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        return base_query, count_query

    async def get_one(self, pizza_id: UUID) -> Pizza:
        pizza = await self.session.get(Pizza, pizza_id)
        if not pizza:
            raise PizzaNotFoundError()
        return pizza

    async def create(self, data: PizzaCreate) -> Pizza:
        stmt = select(Pizza).where(Pizza.name == data.name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise PizzaAlreadyExistsError()

        pizza_data = data.model_dump(exclude={"default_topping_ids"})

        # convert to str from HttpUrl
        pizza_data["image_url"] = str(data.image_url) if data.image_url else None

        pizza = Pizza(**pizza_data)

        # Attach toppings if provided
        if data.default_topping_ids:
            topping_stmt = select(Topping).where(
                Topping.id.in_(data.default_topping_ids)
            )
            toppings = (await self.session.scalars(topping_stmt)).all()
            pizza.default_toppings.extend(toppings)

        self.session.add(pizza)
        await self.session.commit()
        await self.session.refresh(pizza)
        return pizza

    async def update(self, pizza_id: UUID, data: PizzaUpdate) -> Pizza:
        pizza = await self.get_one(pizza_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != pizza.name:
            stmt = select(Pizza).where(Pizza.name == update_data["name"])
            existing = await self.session.scalar(stmt)
            if existing:
                raise PizzaAlreadyExistsError()

        # convert to str from HttpUrl
        if "image_url" in update_data and update_data["image_url"] is not None:
            update_data["image_url"] = str(update_data["image_url"])

        # handle topping-ids separately
        topping_ids = update_data.pop("default_topping_ids", None)
        if topping_ids is not None:
            if topping_ids == []:
                pizza.default_toppings.clear()
            else:
                topping_stmt = select(Topping).where(Topping.id.in_(topping_ids))
                toppings = (await self.session.scalars(topping_stmt)).all()
                pizza.default_toppings.clear()
                pizza.default_toppings.extend(toppings)

        # Apply remaining fields
        for field, value in update_data.items():
            setattr(pizza, field, value)

        self.session.add(pizza)
        await self.session.commit()
        await self.session.refresh(pizza)
        return pizza

    async def delete(self, pizza_id: UUID):
        pizza = await self.get_one(pizza_id)
        await self.session.delete(pizza)
        await self.session.commit()


class ToppingService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(
        self,
        category: str | None = None,
        vegetarian_only: bool | None = None,
    ):
        stmt = select(Topping)

        if category:
            try:
                enum_category = ToppingCategory(category)
                stmt = stmt.where(Topping.category == enum_category)
            except ValueError:
                return []

        if vegetarian_only is True:
            # veg toppings
            stmt = stmt.where(Topping.is_vegetarian)
        if vegetarian_only is False:
            # non-veg toppings
            stmt = stmt.where(Topping.is_vegetarian == False)

        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: ToppingCreate) -> Topping:
        stmt = select(Topping).where(Topping.name == data.name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise ToppingAlreadyExistsError()

        topping_data = data.model_dump()

        topping_data["image_url"] = str(data.image_url) if data.image_url else None

        topping = Topping(**topping_data)

        self.session.add(topping)
        await self.session.commit()
        await self.session.refresh(topping)
        return topping

    async def get_one(self, topping_id: UUID) -> Topping:
        topping = await self.session.get(Topping, topping_id)
        if not topping:
            raise ToppingNotFoundError()
        return topping

    async def update(self, topping_id: UUID, data: ToppingUpdate) -> Topping:
        topping = await self.get_one(topping_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != topping.name:
            stmt = select(Topping).where(Topping.name == update_data["name"])
            existing = await self.session.scalar(stmt)
            if existing:
                raise ToppingAlreadyExistsError()

        if "image_url" in update_data and update_data["image_url"] is not None:
            update_data["image_url"] = str(update_data["image_url"])

        for field, value in update_data.items():
            setattr(topping, field, value)

        self.session.add(topping)
        await self.session.commit()
        await self.session.refresh(topping)
        return topping

    async def delete(self, topping_id: UUID):
        topping = await self.get_one(topping_id)
        await self.session.delete(topping)
        await self.session.commit()


class SizeService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(self):
        stmt = select(Size)
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: SizeCreate) -> Size:
        stmt = select(Size).where(Size.name == data.name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise SizeAlreadyExistsError()

        size_data = data.model_dump()

        size = Size(**size_data)

        self.session.add(size)
        await self.session.commit()
        await self.session.refresh(size)
        return size

    async def get_one(
        self,
        size_id: UUID,
    ) -> Size:
        size = await self.session.get(Size, size_id)
        if not size:
            raise SizeNotFoundError()
        return size

    async def update(self, size_id: UUID, data: SizeUpdate) -> Size:
        size = await self.get_one(size_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != size.name:
            stmt = select(Size).where(Size.name == update_data["name"])
            existing = await self.session.scalar(stmt)
            if existing:
                raise SizeAlreadyExistsError()

        for field, value in update_data.items():
            setattr(size, field, value)

        self.session.add(size)
        await self.session.commit()
        await self.session.refresh(size)
        return size

    async def delete(
        self,
        size_id: UUID,
    ):
        size = await self.get_one(size_id)
        await self.session.delete(size)
        await self.session.commit()


class CrustService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(self):
        stmt = select(Crust)
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: CrustCreate) -> Crust:
        stmt = select(Crust).where(Crust.name == data.name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise CrustAlreadyExistsError()

        crust_data = data.model_dump()

        crust = Crust(**crust_data)

        self.session.add(crust)
        await self.session.commit()
        await self.session.refresh(crust)
        return crust

    async def get_one(
        self,
        crust_id: UUID,
    ) -> Crust:
        crust = await self.session.get(Crust, crust_id)
        if not crust:
            raise CrustNotFoundError()
        return crust

    async def update(self, crust_id: UUID, data: CrustUpdate) -> Crust:
        crust = await self.get_one(crust_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != crust.name:
            stmt = select(Crust).where(Crust.name == update_data["name"])
            existing = await self.session.scalar(stmt)
            if existing:
                raise CrustAlreadyExistsError()

        for field, value in update_data.items():
            setattr(crust, field, value)

        self.session.add(crust)
        await self.session.commit()
        await self.session.refresh(crust)
        return crust

    async def delete(
        self,
        crust_id: UUID,
    ):
        crust = await self.get_one(crust_id)
        await self.session.delete(crust)
        await self.session.commit()
