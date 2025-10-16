from sqlalchemy import update, select, func
from app.core.database import AsyncSession
from app.core.exceptions import MaxAddressesExceededError
from app.auth.model import User
from app.address.schema import AddressCreate
from app.address.model import Address
from app.address.constants import MAX_ADDRESSES_PER_USER


class AddressesService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: AddressCreate, user: User):
        count_result = await self.session.scalar(
            select(func.count()).select_from(Address).where(Address.user_id == user.id)
        )
        address_count = count_result or 0
        if address_count >= MAX_ADDRESSES_PER_USER:
            raise MaxAddressesExceededError()

        address_data_dict = data.model_dump()
        if address_data_dict.get("is_default"):
            await self.session.execute(
                update(Address)
                .where(Address.user_id == user.id, Address.is_default == True)
                .values(is_default=False)
            )

        new_address = Address(**address_data_dict, user_id=user.id)
        self.session.add(new_address)
        await self.session.commit()
        await self.session.refresh(new_address)
        return new_address
