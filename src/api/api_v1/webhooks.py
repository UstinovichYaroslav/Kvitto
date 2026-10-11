from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse

from api.api_v1.dependencies import payment_service
from infrastructure.errors import PaymentNotFoundError
from infrastructure.services import PaymentService
from schemas.payment import (
    WebhookErrorResponse,
    WebhookRequest,
    WebhookResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/bank")
async def webhook_bank(
    webhook_data: WebhookRequest,
    payment_svc: Annotated[PaymentService, Depends(payment_service)],
) -> WebhookResponse:
    try:
        return await payment_svc.process_webhook(webhook_data)
    except PaymentNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found",
        ) from None
    except ValueError as e:
        if str(e) == "invalid_transition":
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content=WebhookErrorResponse(error="invalid_transition").model_dump(),
            )
        raise
