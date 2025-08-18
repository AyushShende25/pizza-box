from sqlalchemy import select
from uuid import UUID
from app.menu.model import Pizza, Topping
from app.menu.schema import PizzaCreate, PizzaUpdate
from app.core.database import AsyncSession
from app.core.exceptions import PizzaAlreadyExistsError, PizzaNotFoundError


class PizzaService:
    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session

    async def get_all(self):
        stmt = select(Pizza)
        result = await self.session.scalars(stmt)
        return result.all()

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

    async def update(self, pizza_id: UUID, data: PizzaUpdate):
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
