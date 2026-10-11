from typing import Annotated

from fastapi import APIRouter, Depends, status

from api.api_v1.dependencies import tariff_service
from infrastructure.errors import (
    TariffNotFoundError,
    handle_tariff_not_found,
)
from infrastructure.services import TariffService
from schemas.tariff import (
    TariffCreate,
    TariffPartialUpdate,
    TariffResponse,
    TariffUpdate,
)

router = APIRouter(prefix="/tariffs", tags=["tariffs"])


@router.get("")
async def get_tariffs(
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> list[TariffResponse]:
    return await tariff_svc.get_all_tariffs()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
)
async def create_tariff(
    tariff_data: TariffCreate,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> TariffResponse:
    return await tariff_svc.create_tariff(tariff_data)


@router.get(
    "/{tariff_id}",
)
async def get_tariff(
    tariff_id: int,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> TariffResponse:
    try:
        return await tariff_svc.get_tariff_by_id(tariff_id)
    except TariffNotFoundError:
        handle_tariff_not_found()


@router.put("/{tariff_id}")
async def update_tariff(
    tariff_id: int,
    tariff_data: TariffUpdate,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> TariffResponse:
    try:
        return await tariff_svc.update_tariff(tariff_id, tariff_data)
    except TariffNotFoundError:
        handle_tariff_not_found()


@router.patch("/{tariff_id}")
async def partial_update_tariff(
    tariff_id: int,
    tariff_data: TariffPartialUpdate,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> TariffResponse:
    try:
        return await tariff_svc.partial_update_tariff(tariff_id, tariff_data)
    except TariffNotFoundError:
        handle_tariff_not_found()


@router.delete("/{tariff_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tariff(
    tariff_id: int,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
) -> None:
    try:
        await tariff_svc.delete_tariff(tariff_id)
    except TariffNotFoundError:
        handle_tariff_not_found()
