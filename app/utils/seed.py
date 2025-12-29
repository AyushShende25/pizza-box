from sqlalchemy import select
from pathlib import Path
from decimal import Decimal
import json
from app.core.database import async_session
from app.auth.model import User, UserRole
from app.auth.utils import get_password_hash
from app.menu.model import Size, Crust, Pizza, Topping, ToppingCategory, PizzaCategory

DATA_FILE = Path(__file__).parent / "dummy_data.json"


async def seed_data():
    data = json.loads(DATA_FILE.read_text())
    async with async_session() as session:
        for u in data.get("users", []):
            user = await session.scalar(select(User).where(User.email == u["email"]))
            if not user:
                user = User(
                    email=u["email"],
                    first_name=u["first_name"],
                    last_name=u["last_name"],
                    password_hash=get_password_hash(u["password"]),
                    role=UserRole[u["role"]],
                    is_verified=u.get("is_verified", False),
                )
                session.add(user)
        await session.flush()

        menu = data.get("menu", {})

        topping_map = {}

        for s in menu.get("sizes", []):
            if not await session.scalar(select(Size).where(Size.name == s["name"])):
                session.add(Size(**s))

        for c in menu.get("crusts", []):
            if not await session.scalar(select(Crust).where(Crust.name == c["name"])):
                session.add(Crust(**c))

        for t in menu.get("toppings", []):
            topping = await session.scalar(
                select(Topping).where(Topping.name == t["name"])
            )
            if not topping:
                topping = Topping(
                    name=t["name"],
                    price=Decimal(str(t["price"])),
                    category=ToppingCategory[t["category"]],
                    is_vegetarian=t["is_vegetarian"],
                )
                session.add(topping)
            topping_map[t["name"]] = topping
        await session.flush()

        for p in menu.get("pizzas", []):
            if await session.scalar(select(Pizza).where(Pizza.name == p["name"])):
                continue

            pizza = Pizza(
                name=p["name"],
                description=p["description"],
                base_price=Decimal(str(p["base_price"])),
                category=PizzaCategory[p["category"]],
                featured=p.get("featured", False),
            )

            for topping_name in p.get("default_toppings", []):
                topping = topping_map.get(topping_name)
                if topping:
                    pizza.default_toppings.append(topping)

            session.add(pizza)

        await session.commit()


if __name__ == "__main__":
    import asyncio

    asyncio.run(seed_data())
