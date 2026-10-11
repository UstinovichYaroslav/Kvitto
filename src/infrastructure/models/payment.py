from datetime import datetime
from enum import Enum

from sqlalchemy import ForeignKey, Integer, String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from kvitto.infrastructure.models.base import Base


class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentMethod(str, Enum):
    CARD = "card"
    SBP = "sbp"
    INSTALLMENT = "installment"


class Payment(Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=PaymentStatus.PENDING)
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # в копейках
    discount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)  # в копейках
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    installment_months: Mapped[int | None] = mapped_column(Integer, nullable=True)
    schedule: Mapped[list[int] | None] = mapped_column(JSON, nullable=True)  # список сумм в копейках
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True,
    )
