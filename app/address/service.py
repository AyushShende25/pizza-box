from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.address.constants import MAX_ADDRESSES_PER_USER
from app.address.model import Address
from app.address.schema import AddressCreate, AddressUpdate
from app.core.exceptions import (
    BadRequestError,
    EntityNotFoundError,
)


class AddressService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        data: AddressCreate,
        user_id: UUID,
    ) -> Address:
        stmt = (
            select(func.count()).select_from(Address).where(Address.user_id == user_id)
        )
        count_result = await self.session.execute(stmt)

        address_count = count_result.scalar_one() or 0

        if address_count >= MAX_ADDRESSES_PER_USER:
            raise BadRequestError(
                error_code="MAX_ADDRESSES_PER_USER_EXCEEDED",
                message="User already has too many addresses",
            )

        address_data_dict = data.model_dump()

        # for first address set is_default to True
        # If not first address set the is_default of current default-address to false
        if address_count == 0:
            address_data_dict["is_default"] = True
        elif address_data_dict.get("is_default"):
            await self.session.execute(
                update(Address)
                .where(Address.user_id == user_id, Address.is_default.is_(True))
                .values(is_default=False)
            )

        new_address = Address(
            **address_data_dict,
            user_id=user_id,
        )
        self.session.add(new_address)

        await self.session.commit()
        await self.session.refresh(new_address)
        return new_address

    async def get_all(
        self,
        user_id: UUID,
    ) -> list[Address]:
        stmt = (
            select(Address)
            .where(Address.user_id == user_id)
            .order_by(
                Address.is_default.desc(),
                Address.created_at.desc(),
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_one(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> Address:
        stmt = select(Address).where(
            Address.id == address_id, Address.user_id == user_id
        )
        result = await self.session.execute(stmt)
        address = result.scalar_one_or_none()

        if not address:
            raise EntityNotFoundError(
                error_code="ADDRESS_NOT_FOUND",
                message=f"Address with id {address_id} does not exists",
            )

        return address

    async def update(
        self,
        address_id: UUID,
        data: AddressUpdate,
        user_id: UUID,
    ) -> Address:
        address = await self.get_one(
            address_id=address_id,
            user_id=user_id,
        )

        update_data = data.model_dump(exclude_unset=True)

        # Unset the existing default address
        if update_data.get("is_default"):
            await self.session.execute(
                update(Address)
                .where(Address.user_id == user_id, Address.is_default.is_(True))
                .values(is_default=False)
            )

        for field, value in update_data.items():
            setattr(address, field, value)

        self.session.add(address)
        await self.session.commit()
        await self.session.refresh(address)
        return address

    async def delete(
        self,
        address_id: UUID,
        user_id: UUID,
    ) -> None:
        address = await self.get_one(
            address_id=address_id,
            user_id=user_id,
        )

        is_default = address.is_default

        await self.session.delete(address)
        await self.session.commit()

        if is_default:
            result = await self.session.execute(
                select(Address)
                .where(Address.user_id == user_id, Address.id != address_id)
                .limit(1)
            )
            another_address = result.scalar_one_or_none()
            if another_address:
                another_address.is_default = True
                await self.session.commit()
