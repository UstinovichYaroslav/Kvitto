from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import db_helper
from infrastructure.repositories.payment import PaymentRepository
from infrastructure.repositories.tariff import TariffRepository
from infrastructure.services.payment import PaymentService
from infrastructure.services.tariff import TariffService


async def payment_repository(
    session: Annotated[AsyncSession, Depends(db_helper.async_session_getter)],
) -> PaymentRepository:
    return PaymentRepository(session=session)


async def tariff_repository(
    session: Annotated[AsyncSession, Depends(db_helper.async_session_getter)],
) -> TariffRepository:
    return TariffRepository(session=session)


async def payment_service(
    repository: Annotated[PaymentRepository, Depends(payment_repository)],
) -> PaymentService:
    return PaymentService(session=repository.session)


async def tariff_service(
    repository: Annotated[TariffRepository, Depends(tariff_repository)],
) -> TariffService:
    return TariffService(session=repository.session)
