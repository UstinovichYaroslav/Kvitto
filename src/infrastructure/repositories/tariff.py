from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.models.tariff import Tariff
from schemas.tariff import TariffCreate, TariffPartialUpdate, TariffUpdate


class TariffRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> list[Tariff]:
        stmt = select(Tariff).order_by(Tariff.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, tariff_id: int) -> Tariff | None:
        return await self.session.get(Tariff, tariff_id)

    async def create(self, tariff_data: TariffCreate) -> Tariff:
        tariff = Tariff(**tariff_data.model_dump())
        self.session.add(tariff)
        await self.session.flush()
        await self.session.refresh(tariff)
        return tariff

    async def update(self, tariff: Tariff, tariff_data: TariffUpdate) -> Tariff:
        """Полное обновление тарифа"""
        for key, value in tariff_data.model_dump().items():
            setattr(tariff, key, value)
        await self.session.flush()
        await self.session.refresh(tariff)
        return tariff

    async def partial_update(
        self, tariff: Tariff, tariff_data: TariffPartialUpdate,
    ) -> Tariff:
        """Частичное обновление тарифа"""
        for key, value in tariff_data.model_dump(exclude_unset=True).items():
            setattr(tariff, key, value)
        await self.session.flush()
        await self.session.refresh(tariff)
        return tariff

    async def delete(self, tariff: Tariff) -> None:
        """Удаление тарифа"""
        await self.session.delete(tariff)
        await self.session.flush()
