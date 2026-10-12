from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from infrastructure.models.payment import PaymentMethod


class PaymentCreateRequest(BaseModel):
    tariff_id: int = Field(gt=0)
    email: EmailStr
    method: PaymentMethod
    installment_months: int | None = Field(None, ge=3, le=12)
    promo_code: str | None = Field(None, max_length=50)

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
    tariff_id: int = Field(gt=0)
    amount: int = Field(ge=0)
    discount: int = Field(ge=0)
    method: str
    email: EmailStr
    installment_months: int | None = Field(None, ge=3, le=12)
    schedule: list[int] | None = None
    idempotency_key: str | None = Field(None, max_length=100)


class PaymentUpdate(BaseModel):
    status: str
    amount: int = Field(ge=0)
    discount: int = Field(ge=0)
    method: str
    email: EmailStr
    installment_months: int = Field(ge=3, le=12)
    schedule: list[int]
    idempotency_key: str = Field(max_length=100)


class PaymentPartialUpdate(BaseModel):
    status: str | None = None
    amount: int | None = Field(None, ge=0)
    discount: int | None = Field(None, ge=0)
    method: str | None = None
    email: EmailStr | None = None
    installment_months: int | None = Field(None, ge=3, le=12)
    schedule: list[int] | None = None
    idempotency_key: str | None = Field(None, max_length=100)


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
    payment_id: int = Field(gt=0)
    status: str


class WebhookResponse(BaseModel):
    result: str = "ok"


class WebhookErrorResponse(BaseModel):
    error: str
