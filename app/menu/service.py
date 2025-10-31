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
from sqlalchemy.ext.asyncio import AsyncSession
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
        featured: bool | None = None,
    ):
        skip = (page - 1) * limit

        field, order = self._parse_sort_params(sort_by)
        sort_column = getattr(Pizza, field, Pizza.created_at)
        sort_order = asc(sort_column) if order.lower() == "asc" else desc(sort_column)

        base_query, count_query = self._build_queries(
            category, name, is_available, featured
        )

        total = await self.session.scalar(count_query)

        stmt = (
            base_query.options(selectinload(Pizza.default_toppings))
            .order_by(sort_order)
            .limit(limit)
            .offset(skip)
        )

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
            field = field if field in valid_fields else "created_at"
            order = order if order.lower() in {"asc", "desc"} else "asc"

            return field, order
        except ValueError:
            return "created_at", "desc"

    def _build_queries(
        self,
        category: PizzaCategory | None,
        name: str | None,
        is_available: bool | None,
        featured: bool | None,
    ):
        base_query = select(Pizza)
        count_query = select(func.count()).select_from(Pizza)

        filters = []

        if category:
            filters.append(Pizza.category == category)

        if name:
            filters.append(Pizza.name.ilike(f"%{name}%"))

        if is_available is not None:
            filters.append(Pizza.is_available == is_available)

        if featured is not None:
            filters.append(Pizza.featured == featured)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        return base_query, count_query

    async def get_one(self, pizza_id: UUID, load_toppings: bool = True) -> Pizza:
        stmt = select(Pizza).where(Pizza.id == pizza_id)
        if load_toppings:
            stmt = stmt.options(selectinload(Pizza.default_toppings))
        pizza = await self.session.scalar(stmt)
        if not pizza:
            raise PizzaNotFoundError()
        return pizza

    async def create(self, data: PizzaCreate) -> Pizza:
        await self._check_duplicate_name(data.name)

        pizza_data = data.model_dump(exclude={"default_topping_ids"})

        # convert to str from HttpUrl
        pizza_data["image_url"] = str(data.image_url) if data.image_url else None

        pizza = Pizza(**pizza_data)

        # Attach toppings if provided
        if data.default_topping_ids:
            toppings = await self._get_toppings_by_ids(data.default_topping_ids)
            pizza.default_toppings.extend(toppings)

        self.session.add(pizza)
        await self.session.commit()
        loaded_pizza = await self.session.execute(
            select(Pizza)
            .options(selectinload(Pizza.default_toppings))
            .where(Pizza.id == pizza.id)
        )
        return loaded_pizza.scalar_one()

    async def update(self, pizza_id: UUID, data: PizzaUpdate) -> Pizza:
        pizza = await self.get_one(pizza_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != pizza.name:
            await self._check_duplicate_name(update_data["name"])

        # convert to str from HttpUrl
        if "image_url" in update_data and update_data["image_url"] is not None:
            update_data["image_url"] = str(update_data["image_url"])

        # handle topping-ids separately
        topping_ids = update_data.pop("default_topping_ids", None)
        if topping_ids is not None:
            if topping_ids == []:
                pizza.default_toppings.clear()
            else:
                toppings = await self._get_toppings_by_ids(topping_ids)
                pizza.default_toppings.clear()
                pizza.default_toppings.extend(toppings)

        # Apply remaining fields
        for field, value in update_data.items():
            setattr(pizza, field, value)

        self.session.add(pizza)
        await self.session.commit()
        loaded_pizza = await self.session.execute(
            select(Pizza)
            .options(selectinload(Pizza.default_toppings))
            .where(Pizza.id == pizza.id)
        )
        return loaded_pizza.scalar_one()

    async def delete(self, pizza_id: UUID):
        pizza = await self.get_one(pizza_id, load_toppings=False)
        await self.session.delete(pizza)
        await self.session.commit()

    async def _check_duplicate_name(self, name: str, exclude_id: UUID | None = None):
        stmt = select(Pizza).where(Pizza.name == name)
        if exclude_id:
            stmt = stmt.where(Pizza.id != exclude_id)

        existing = await self.session.scalar(stmt)
        if existing:
            raise PizzaAlreadyExistsError()

    async def _get_toppings_by_ids(self, topping_ids: list[UUID]) -> list[Topping]:
        stmt = select(Topping).where(Topping.id.in_(topping_ids))
        result = await self.session.scalars(stmt)
        return list(result.all())


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
        is_available: bool | None = None,
    ):
        stmt = select(Topping)

        filters = []

        if is_available is not None:
            filters.append(Topping.is_available == is_available)

        if category:
            try:
                enum_category = ToppingCategory(category)
                filters.append(Topping.category == enum_category)
            except ValueError:
                return []

        if vegetarian_only is not None:
            # vegetarian_only: True -> veg toppings
            # vegetarian_only: False -> non-veg toppings
            filters.append(Topping.is_vegetarian == vegetarian_only)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(asc(Topping.name))
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: ToppingCreate) -> Topping:
        await self._check_duplicate_name(data.name)

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
            await self._check_duplicate_name(update_data["name"])

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

    async def _check_duplicate_name(self, name: str):
        stmt = select(Topping).where(Topping.name == name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise ToppingAlreadyExistsError()


class SizeService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(self, available_only: bool = False):
        stmt = select(Size).order_by(asc(Size.sort_order))
        if available_only:
            stmt = stmt.where(Size.is_available == True)
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: SizeCreate) -> Size:
        await self._check_duplicate_name(data.name)

        size = Size(**data.model_dump())
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
            await self._check_duplicate_name(update_data["name"])

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

    async def _check_duplicate_name(self, name: str):
        stmt = select(Size).where(Size.name == name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise SizeAlreadyExistsError()


class CrustService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(self, available_only: bool = False):
        stmt = select(Crust).order_by(asc(Crust.sort_order))
        if available_only:
            stmt = stmt.where(Crust.is_available == True)
        result = await self.session.scalars(stmt)
        return result.all()

    async def create(self, data: CrustCreate) -> Crust:
        await self._check_duplicate_name(data.name)

        crust = Crust(**data.model_dump())
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
            await self._check_duplicate_name(update_data["name"])

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

    async def _check_duplicate_name(self, name: str):
        stmt = select(Crust).where(Crust.name == name)
        existing = await self.session.scalar(stmt)
        if existing:
            raise CrustAlreadyExistsError()
