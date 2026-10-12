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
    async def get_by_idempotency_key(self, key: str) -> Any:
        pass

    @abstractmethod
    async def update(
        self,
        payment: Any,
        payment_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def partial_update(
        self,
        payment: Any,
        payment_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def delete(self, payment: Any) -> None:
        pass

    @abstractmethod
    async def update_status(self, payment: Any, new_status: str) -> Any:
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
        tariff: Any,
        tariff_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def partial_update(
        self,
        tariff: Any,
        tariff_data: Any,
    ) -> Any:
        pass

    @abstractmethod
    async def delete(self, tariff: Any) -> None:
        pass
