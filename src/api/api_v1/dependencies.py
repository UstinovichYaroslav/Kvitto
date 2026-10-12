from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import db_helper
from infrastructure.repositories.interface import IPaymentRepository, ITariffRepository
from infrastructure.repositories.payment import PaymentRepository
from infrastructure.repositories.tariff import TariffRepository
from infrastructure.services.payment import PaymentService
from infrastructure.services.tariff import TariffService


async def payment_repository(
    session: Annotated[AsyncSession, Depends(db_helper.async_session_getter)],
) -> IPaymentRepository:
    return PaymentRepository(session=session)


async def tariff_repository(
    session: Annotated[AsyncSession, Depends(db_helper.async_session_getter)],
) -> ITariffRepository:
    return TariffRepository(session=session)


async def payment_service(
    repository: Annotated[IPaymentRepository, Depends(payment_repository)],
) -> PaymentService:
    return PaymentService(payment_repo=repository)


async def tariff_service(
    repository: Annotated[ITariffRepository, Depends(tariff_repository)],
) -> TariffService:
    return TariffService(tariff_repo=repository)
