from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.errors import TariffNotFoundError
from infrastructure.errors.tariff import TariffInUseError
from infrastructure.repositories.tariff import TariffRepository
from schemas.tariff import (
    TariffCreate,
    TariffPartialUpdate,
    TariffResponse,
    TariffUpdate,
)


class TariffService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.tariff_repo = TariffRepository(session)

    async def get_all_tariffs(self) -> list[TariffResponse]:
        """Возвращает список TariffResponse"""
        tariffs = await self.tariff_repo.get_all()
        return [TariffResponse.model_validate(tariff) for tariff in tariffs]

    async def get_tariff_by_id(self, tariff_id: int) -> TariffResponse:
        """Возвращает TariffResponse или 404"""
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundError(tariff_id)
        return TariffResponse.model_validate(tariff)

    async def init_default_tariffs(self) -> None:
        """Создаёт тарифы при старте, если их нет"""
        await self.initializer.init_default_tariffs()

    async def create_tariff(self, tariff_data: TariffCreate) -> TariffResponse:
        """Создаёт тариф"""
        tariff = await self.tariff_repo.create(tariff_data)
        await self.session.commit()
        return TariffResponse.model_validate(tariff)

    async def update_tariff(
        self,
        tariff_id: int,
        tariff_data: TariffUpdate,
    ) -> TariffResponse:
        """Полное обновление тарифа"""
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundError(tariff_id)
        updated = await self.tariff_repo.update(tariff, tariff_data)
        await self.session.commit()
        return TariffResponse.model_validate(updated)

    async def partial_update_tariff(
        self,
        tariff_id: int,
        tariff_data: TariffPartialUpdate,
    ) -> TariffResponse:
        """Частичное обновление тарифа"""
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundError(tariff_id)
        updated = await self.tariff_repo.partial_update(tariff, tariff_data)
        await self.session.commit()
        return TariffResponse.model_validate(updated)

    async def delete_tariff(self, tariff_id: int) -> None:
        """Удаляет тариф"""
        tariff = await self.tariff_repo.get_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundError(tariff_id)
        try:
            await self.tariff_repo.delete(tariff)
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise TariffInUseError(tariff_id) from error
