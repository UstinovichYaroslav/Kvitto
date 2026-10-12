from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from api.api_v1.dependencies import payment_service, tariff_service
from infrastructure.errors import (
    PaymentNotFoundError,
    TariffNotFoundError,
    handle_internal_error,
    handle_invalid_promo_code,
    handle_payment_not_found,
    handle_tariff_not_found,
    handle_validation_error,
)
from infrastructure.services import PaymentService, TariffService
from schemas.payment import (
    PaymentCreateRequest,
    PaymentPartialUpdate,
    PaymentResponse,
    PaymentUpdate,
)

router = APIRouter(
    prefix="/payments",
    tags=["payments"],
)


@router.get("")
async def get_payments(
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> list[PaymentResponse]:
    return await payment_svc.get_all_payments()


@router.post("")
async def create_payment(
    payment_data: PaymentCreateRequest,
    tariff_svc: Annotated[TariffService, Depends(tariff_service)],
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
    response: Response = None,
) -> PaymentResponse:
    try:
        payment, was_created = await payment_svc.create_payment_with_validation(
            payment_data,
            idempotency_key,
            tariff_svc,
        )
        if was_created:
            response.status_code = status.HTTP_201_CREATED
        else:
            response.status_code = status.HTTP_200_OK
        return payment
    except TariffNotFoundError:
        handle_tariff_not_found()
    except ValueError as e:
        error_msg = str(e)
        if error_msg == "Invalid promo code":
            handle_invalid_promo_code()
        handle_validation_error(error_msg)
    except Exception as e:  # noqa: BLE001
        handle_internal_error(e)


@router.get("/{payment_id}")
async def get_payment(
    payment_id: int,
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> PaymentResponse:
    try:
        return await payment_svc.get_payment_by_id(payment_id)
    except PaymentNotFoundError:
        handle_payment_not_found()


@router.put("/{payment_id}")
async def update_payment(
    payment_id: int,
    payment_data: PaymentUpdate,
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> PaymentResponse:
    try:
        return await payment_svc.update_payment(payment_id, payment_data)
    except PaymentNotFoundError:
        handle_payment_not_found()
    except Exception as e:  # noqa: BLE001
        handle_internal_error(e)


@router.patch("/{payment_id}")
async def partial_update_payment(
    payment_id: int,
    payment_data: PaymentPartialUpdate,
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> PaymentResponse:
    try:
        return await payment_svc.partial_update_payment(payment_id, payment_data)
    except PaymentNotFoundError:
        handle_payment_not_found()
    except Exception as e:  # noqa: BLE001
        handle_internal_error(e)


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: int,
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> None:
    try:
        await payment_svc.delete_payment(payment_id)
    except PaymentNotFoundError:
        handle_payment_not_found()
    except Exception as e:  # noqa: BLE001
        handle_internal_error(e)
