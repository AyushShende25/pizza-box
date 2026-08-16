import math
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import and_, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.core.exceptions import ConflictError, EntityNotFoundError
from app.menu.model import Crust, FoodType, Pizza, Size, Topping, ToppingCategory
from app.menu.schema import (
    CrustCreate,
    CrustUpdate,
    PizzaCreate,
    PizzaSortField,
    PizzaUpdate,
    SizeCreate,
    SizeUpdate,
    SortOrder,
    ToppingCreate,
    ToppingUpdate,
)


async def entity_exists_by_name(
    session: AsyncSession,
    model: type[Any],
    name: str,
    exclude_id: UUID | None = None,
) -> bool:
    stmt = select(model).where(model.name == name)

    if exclude_id is not None:
        stmt = stmt.where(model.id != exclude_id)

    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None


class PizzaService:
    """Service handling business logic for Pizza management."""

    SORT_MAP: ClassVar[dict[PizzaSortField, InstrumentedAttribute]] = {
        "created_at": Pizza.created_at,
        "is_available": Pizza.is_available,
        "is_featured": Pizza.is_featured,
        "name": Pizza.name,
        "base_price": Pizza.base_price,
        "food_type": Pizza.food_type,
    }

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    def _build_filter_queries(
        self,
        food_type: FoodType | None,
        name: str | None,
        is_available: bool | None,
        is_featured: bool | None,
    ):
        base_query = select(Pizza)
        count_query = select(func.count()).select_from(Pizza)

        filters = []

        if food_type:
            filters.append(Pizza.food_type == food_type)

        if name:
            filters.append(Pizza.name.ilike(f"%{name}%"))

        if is_available is not None:
            filters.append(Pizza.is_available == is_available)

        if is_featured is not None:
            filters.append(Pizza.is_featured == is_featured)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        return base_query, count_query

    async def get_all(
        self,
        page: int,
        limit: int,
        sort_by: PizzaSortField,
        order: SortOrder,
        food_type: FoodType | None = None,
        name: str | None = None,
        is_available: bool | None = None,
        is_featured: bool | None = None,
    ):
        skip = (page - 1) * limit

        sort_column = self.SORT_MAP[sort_by]
        sort_order = asc(sort_column) if order == "asc" else desc(sort_column)

        base_query, count_query = self._build_filter_queries(
            food_type=food_type,
            name=name,
            is_available=is_available,
            is_featured=is_featured,
        )

        result = await self.session.execute(count_query)
        total = result.scalar_one() or 0

        stmt = (
            base_query
            .options(selectinload(Pizza.default_toppings))
            .order_by(sort_order)
            .limit(limit)
            .offset(skip)
        )

        result = await self.session.execute(stmt)
        items = result.scalars().all()

        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "pages": math.ceil(total / limit) if total > 0 else 0,
        }

    async def get_one(self, pizza_id: UUID, load_toppings: bool = True) -> Pizza:
        stmt = select(Pizza).where(Pizza.id == pizza_id)
        if load_toppings:
            stmt = stmt.options(selectinload(Pizza.default_toppings))

        result = await self.session.execute(stmt)
        pizza = result.scalar_one_or_none()

        if not pizza:
            raise EntityNotFoundError(
                error_code="PIZZA_NOT_FOUND",
                message="Pizza does not exist",
            )
        return pizza

    async def create(self, data: PizzaCreate) -> Pizza | None:
        exists = await entity_exists_by_name(
            session=self.session,
            model=Pizza,
            name=data.name,
        )
        if exists:
            raise ConflictError(
                error_code="PIZZA_ALREADY_EXISTS",
                message=f"Pizza with name '{data.name}' already exists",
            )

        pizza = Pizza(**data.model_dump(exclude={"default_topping_ids"}, mode="json"))

        # Attach toppings if provided
        if data.default_topping_ids:
            toppings = await self._get_toppings_by_ids(data.default_topping_ids)
            pizza.default_toppings.extend(toppings)

        self.session.add(pizza)
        await self.session.commit()
        return await self.get_one(pizza_id=pizza.id, load_toppings=True)

    async def update(self, pizza_id: UUID, data: PizzaUpdate) -> Pizza | None:
        pizza = await self.get_one(pizza_id=pizza_id, load_toppings=True)

        update_data = data.model_dump(exclude_unset=True, mode="json")

        # check for duplicate name, if name is provided and changed from previous
        if "name" in update_data and update_data["name"] != pizza.name:
            exists = await entity_exists_by_name(
                session=self.session,
                model=Pizza,
                name=update_data["name"],
                exclude_id=pizza.id,
            )
            if exists:
                raise ConflictError(
                    error_code="PIZZA_ALREADY_EXISTS",
                    message=f"Pizza with name '{update_data['name']}' already exists",
                )

        # clear toppings if empty-list else replace
        if "default_topping_ids" in update_data:
            topping_ids = update_data.pop("default_topping_ids")
            if not topping_ids:
                pizza.default_toppings.clear()
            else:
                toppings = await self._get_toppings_by_ids(topping_ids)
                pizza.default_toppings = toppings

        # Apply remaining fields
        for field, value in update_data.items():
            setattr(pizza, field, value)

        self.session.add(pizza)
        await self.session.commit()
        return await self.get_one(pizza_id=pizza.id, load_toppings=True)

    async def delete(self, pizza_id: UUID) -> None:
        pizza = await self.get_one(pizza_id=pizza_id, load_toppings=False)
        await self.session.delete(pizza)
        await self.session.commit()

    async def _get_toppings_by_ids(self, topping_ids: list[UUID]) -> list[Topping]:
        stmt = select(Topping).where(Topping.id.in_(topping_ids))

        result = await self.session.execute(stmt)
        toppings = list(result.scalars().all())

        if len(toppings) != len(set(topping_ids)):
            raise EntityNotFoundError(
                error_code="TOPPING_NOT_FOUND",
                message="One or more specified topping IDs do not exist",
            )

        return toppings


class ToppingService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(
        self,
        category: ToppingCategory | None = None,
        food_type: FoodType | None = None,
        is_available: bool | None = None,
    ):
        stmt = select(Topping)

        filters = []

        if is_available is not None:
            filters.append(Topping.is_available == is_available)

        if category is not None:
            filters.append(Topping.category == category)

        if food_type is not None:
            filters.append(Topping.food_type == food_type)

        if filters:
            stmt = stmt.where(and_(*filters))

        stmt = stmt.order_by(asc(Topping.name))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create(self, data: ToppingCreate) -> Topping:
        exists = await entity_exists_by_name(
            session=self.session,
            model=Topping,
            name=data.name,
        )

        if exists:
            raise ConflictError(
                error_code="TOPPING_ALREADY_EXISTS",
                message=f"Topping with name {data.name} already exists",
            )

        topping = Topping(**data.model_dump(mode="json"))

        self.session.add(topping)
        await self.session.commit()
        await self.session.refresh(topping)
        return topping

    async def get_one(self, topping_id: UUID) -> Topping:
        stmt = select(Topping).where(Topping.id == topping_id)
        result = await self.session.execute(stmt)

        topping = result.scalar_one_or_none()

        if not topping:
            raise EntityNotFoundError(
                error_code="TOPPING_NOT_FOUND",
                message="Topping does not exist",
            )
        return topping

    async def update(self, topping_id: UUID, data: ToppingUpdate) -> Topping:
        topping = await self.get_one(topping_id)

        update_data = data.model_dump(exclude_unset=True, mode="json")

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != topping.name:
            exists = await entity_exists_by_name(
                session=self.session,
                model=Topping,
                name=update_data["name"],
                exclude_id=topping.id,
            )
            if exists:
                raise ConflictError(
                    error_code="TOPPING_ALREADY_EXISTS",
                    message=f"Topping with name {update_data['name']} already exists",
                )

        for field, value in update_data.items():
            setattr(topping, field, value)

        self.session.add(topping)
        await self.session.commit()
        await self.session.refresh(topping)
        return topping

    async def delete(self, topping_id: UUID) -> None:
        topping = await self.get_one(topping_id)
        await self.session.delete(topping)
        await self.session.commit()


class SizeService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(
        self,
        is_available: bool | None = None,
    ):
        stmt = select(Size).order_by(asc(Size.sort_order))

        if is_available is not None:
            stmt = stmt.where(Size.is_available == is_available)

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def create(self, data: SizeCreate) -> Size:
        exists = await entity_exists_by_name(
            session=self.session,
            model=Size,
            name=data.name,
        )

        if exists:
            raise ConflictError(
                error_code="SIZE_ALREADY_EXISTS",
                message=f"Size with name {data.name} already exists",
            )

        size = Size(**data.model_dump())

        self.session.add(size)
        await self.session.commit()
        await self.session.refresh(size)
        return size

    async def get_one(
        self,
        size_id: UUID,
    ) -> Size:
        stmt = select(Size).where(Size.id == size_id)
        result = await self.session.execute(stmt)

        size = result.scalar_one_or_none()

        if not size:
            raise EntityNotFoundError(
                error_code="SIZE_NOT_FOUND",
                message="Size does not exist",
            )
        return size

    async def update(self, size_id: UUID, data: SizeUpdate) -> Size:
        size = await self.get_one(size_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != size.name:
            exists = await entity_exists_by_name(
                session=self.session,
                model=Size,
                name=update_data["name"],
                exclude_id=size.id,
            )

            if exists:
                raise ConflictError(
                    error_code="SIZE_ALREADY_EXISTS",
                    message=f"Size with name {update_data['name']} already exists",
                )

        for field, value in update_data.items():
            setattr(size, field, value)

        self.session.add(size)
        await self.session.commit()
        await self.session.refresh(size)
        return size

    async def delete(
        self,
        size_id: UUID,
    ) -> None:
        size = await self.get_one(size_id)
        await self.session.delete(size)
        await self.session.commit()


class CrustService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(
        self,
        is_available: bool | None = None,
    ):
        stmt = select(Crust).order_by(asc(Crust.sort_order))

        if is_available is not None:
            stmt = stmt.where(Crust.is_available == is_available)

        result = await self.session.execute(stmt)

        return result.scalars().all()

    async def create(self, data: CrustCreate) -> Crust:
        exists = await entity_exists_by_name(
            session=self.session,
            model=Crust,
            name=data.name,
        )
        if exists:
            raise ConflictError(
                error_code="CRUST_ALREADY_EXISTS",
                message=f"Crust with name {data.name} already exists",
            )

        crust = Crust(**data.model_dump())
        self.session.add(crust)
        await self.session.commit()
        await self.session.refresh(crust)
        return crust

    async def get_one(
        self,
        crust_id: UUID,
    ) -> Crust:
        stmt = select(Crust).where(Crust.id == crust_id)
        result = await self.session.execute(stmt)

        crust = result.scalar_one_or_none()

        if not crust:
            raise EntityNotFoundError(
                error_code="CRUST_NOT_FOUND",
                message="Crust does not exist",
            )
        return crust

    async def update(self, crust_id: UUID, data: CrustUpdate) -> Crust:
        crust = await self.get_one(crust_id)

        update_data = data.model_dump(exclude_unset=True)

        # check for duplicate name, if provided and changed
        if "name" in update_data and update_data["name"] != crust.name:
            exists = await entity_exists_by_name(
                session=self.session,
                model=Crust,
                name=update_data["name"],
                exclude_id=crust.id,
            )

            if exists:
                raise ConflictError(
                    error_code="CRUST_ALREADY_EXISTS",
                    message=f"Crust with name {update_data['name']} already exists",
                )

        for field, value in update_data.items():
            setattr(crust, field, value)

        self.session.add(crust)
        await self.session.commit()
        await self.session.refresh(crust)
        return crust

    async def delete(
        self,
        crust_id: UUID,
    ) -> None:
        crust = await self.get_one(crust_id)
        await self.session.delete(crust)
        await self.session.commit()
