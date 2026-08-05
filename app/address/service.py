from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.address.constants import MAX_ADDRESSES_PER_USER
from app.address.model import Address
from app.address.schema import AddressCreate, AddressUpdate
from app.auth.model import User
from app.core.exceptions import (
    BadRequestError,
    EntityNotFoundError,
)


class AddressesService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AddressCreate, user: User):
        count_result = await self.session.scalar(
            select(func.count()).select_from(Address).where(Address.user_id == user.id)
        )
        address_count = count_result or 0
        if address_count >= MAX_ADDRESSES_PER_USER:
            raise BadRequestError(
                error_code="MAX_ADDRESSES_PER_USER_EXCEEDED",
                message="User already has too many addresses",
            )

        address_data_dict = data.model_dump()

        if address_count == 0:
            address_data_dict["is_default"] = True
        elif address_data_dict.get("is_default"):
            await self.session.execute(
                update(Address)
                .where(Address.user_id == user.id, Address.is_default.is_(True))
                .values(is_default=False)
            )

        new_address = Address(**address_data_dict, user_id=user.id)
        self.session.add(new_address)

        await self.session.commit()
        await self.session.refresh(new_address)
        return new_address

    async def get_all(self, user: User):
        return (
            await self.session.scalars(
                select(Address).where(Address.user_id == user.id)
            )
        ).all()

    async def get_one(self, address_id: UUID, user_id: UUID):
        address = await self.session.scalar(
            select(Address).where(Address.id == address_id, Address.user_id == user_id)
        )
        if not address:
            raise EntityNotFoundError(
                error_code="ADDRESS_NOT_FOUND",
                message="Address with that id does not exists",
            )
        return address

    async def update(self, address_id: UUID, data: AddressUpdate, user: User):
        address = await self.get_one(address_id, user.id)

        update_data = data.model_dump(exclude_unset=True)

        if update_data.get("is_default"):
            await self.session.execute(
                update(Address)
                .where(Address.user_id == user.id, Address.is_default.is_(True))
                .values(is_default=False)
            )

        for f, v in update_data.items():
            setattr(address, f, v)

        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete(self, address_id: UUID, user: User):
        address = await self.get_one(address_id, user.id)

        is_default = address.is_default

        await self.session.delete(address)
        await self.session.commit()

        if is_default:
            another = await self.session.scalar(
                select(Address)
                .where(Address.user_id == user.id, Address.id != address.id)
                .limit(1)
            )
            if another:
                another.is_default = True
                await self.session.commit()
