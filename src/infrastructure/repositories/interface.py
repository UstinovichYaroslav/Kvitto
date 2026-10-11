from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession


class IRepository(ABC):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self.session = session


class IPaymentRepository(IRepository):
    @abstractmethod
    async def create(self, payment_data: Any) -> Any:
        pass

    @abstractmethod
    async def get_all(self) -> list[Any]:
        pass

    @abstractmethod
    async def get_by_id(self, payment_id: int) -> Any:
        pass

    @abstractmethod
    async def update(
        self,
        payment: Any,
        payment_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def delete(self, payment: Any) -> None:
        pass


class ITariffRepository(IRepository):
    @abstractmethod
    async def create(self, tariff_data: Any) -> Any:
        pass

    @abstractmethod
    async def get_all(self) -> list[Any]:
        pass

    @abstractmethod
    async def get_by_id(self, tariff_id: int) -> Any:
        pass

    @abstractmethod
    async def update(
        self,
        tariff_id: int,
        tariff_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def delete(self, tariff_id: int) -> None:
        pass
