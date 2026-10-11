from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from infrastructure.models.payment import PaymentMethod


class PaymentCreateRequest(BaseModel):
    tariff_id: int
    email: str
    method: PaymentMethod
    installment_months: int | None = Field(None, ge=3, le=12)
    promo_code: str | None = None

    @field_validator("installment_months")
    @classmethod
    def validate_installment(cls, v: int | None, info: ValidationInfo) -> int | None:
        if v is not None and info.data.get("method") != PaymentMethod.INSTALLMENT:
            msg = "installment_months only allowed for installment method"
            raise ValueError(msg)
        if info.data.get("method") == PaymentMethod.INSTALLMENT and v is None:
            msg = "installment_months required for installment method"
            raise ValueError(msg)
        return v


class PaymentCreate(BaseModel):
    tariff_id: int
    amount: int
    discount: int
    method: str
    email: str
    installment_months: int | None = None
    schedule: list[int] | None = None
    idempotency_key: str | None = None


class PaymentUpdate(BaseModel):
    status: str
    amount: int
    discount: int
    method: str
    email: str
    installment_months: int
    schedule: list[int]
    idempotency_key: str


class PaymentPartialUpdate(BaseModel):
    status: str | None = None
    amount: int | None = None
    discount: int | None = None
    method: str | None = None
    email: str | None = None
    installment_months: int | None = None
    schedule: list[int] | None = None
    idempotency_key: str | None = None


class PaymentResponse(BaseModel):
    id: int
    status: str
    tariff_id: int
    amount: int  # в копейках
    discount: int  # в копейках
    method: str
    installment_months: int | None = None
    schedule: list[int] | None = None  # список сумм в копейках
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookRequest(BaseModel):
    payment_id: int
    status: str


class WebhookResponse(BaseModel):
    result: str = "ok"


class WebhookErrorResponse(BaseModel):
    error: str
