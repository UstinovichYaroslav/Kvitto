from typing import ClassVar

from infrastructure.errors import PaymentNotFoundError
from infrastructure.errors.payment import InvalidTransitionError
from infrastructure.models.payment import PaymentMethod, PaymentStatus
from infrastructure.repositories.interface import IPaymentRepository
from infrastructure.services.calculators import (
    DiscountCalculator,
    InstallmentCalculator,
)
from infrastructure.services.handlers import WebhookHandler
from infrastructure.services.validators import PromoCodeValidator
from schemas.payment import (
    PaymentCreate,
    PaymentCreateRequest,
    PaymentPartialUpdate,
    PaymentResponse,
    PaymentUpdate,
)


class PaymentStateMachine:
    VALID_TRANSITIONS: ClassVar[dict[PaymentStatus, frozenset[PaymentStatus]]] = {
        PaymentStatus.PENDING: frozenset(
            {PaymentStatus.SUCCEEDED, PaymentStatus.FAILED}
        ),
        PaymentStatus.SUCCEEDED: frozenset({PaymentStatus.REFUNDED}),
        PaymentStatus.FAILED: frozenset(),
        PaymentStatus.REFUNDED: frozenset(),
    }

    @classmethod
    def can_transition(cls, src: PaymentStatus, dst: PaymentStatus) -> bool:
        return dst in cls.VALID_TRANSITIONS.get(src, frozenset())

    @classmethod
    def assert_transition(cls, src: PaymentStatus, dst: PaymentStatus) -> None:
        if not cls.can_transition(src, dst):
            raise InvalidTransitionError(src, dst)


class PaymentService:
    VALID_TRANSITIONS = {  # noqa: RUF012
        PaymentStatus.PENDING: [PaymentStatus.SUCCEEDED, PaymentStatus.FAILED],
        PaymentStatus.SUCCEEDED: [PaymentStatus.REFUNDED],
        PaymentStatus.FAILED: [],
        PaymentStatus.REFUNDED: [],
    }

    def __init__(self, payment_repo: IPaymentRepository) -> None:
        self.payment_repo = payment_repo
        self.webhook_handler = WebhookHandler(payment_repo)

    async def get_all_payments(self) -> list[PaymentResponse]:
        """Возвращает список PaymentResponse"""
        payments = await self.payment_repo.get_all()
        return [PaymentResponse.model_validate(payment) for payment in payments]

    async def get_payment_by_id(self, payment_id: int) -> PaymentResponse:
        """Возвращает PaymentResponse или 404"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        return PaymentResponse.model_validate(payment)

    async def get_payment_by_idempotency_key(self, key: str) -> PaymentResponse | None:
        """Возвращает PaymentResponse по idempotency key или None"""
        payment = await self.payment_repo.get_by_idempotency_key(key)
        if payment:
            return PaymentResponse.model_validate(payment)
        return None

    async def create_payment(self, payment_data: PaymentCreate) -> PaymentResponse:
        """Создаёт платёж и возвращает PaymentResponse"""
        payment = await self.payment_repo.create(payment_data)
        return PaymentResponse.model_validate(payment)

    async def update_payment_status(
        self,
        payment_id: int,
        new_status: str,
    ) -> PaymentResponse:
        """Обновляет статус платежа и возвращает PaymentResponse"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        PaymentStateMachine.assert_transition(payment.status, new_status)
        updated_payment = await self.payment_repo.update_status(payment, new_status)
        return PaymentResponse.model_validate(updated_payment)

    async def create_payment_with_validation(
        self,
        payment_data: PaymentCreateRequest,
        idempotency_key: str | None,
        tariff_service: "TariffService",  # noqa: F821
    ) -> tuple[PaymentResponse, bool]:
        """Создаёт платёж с валидацией. Возвращает (payment, was_created)"""
        # Проверка idempotency
        if idempotency_key:
            existing_payment = await self.get_payment_by_idempotency_key(
                idempotency_key,
            )
            if existing_payment:
                return existing_payment, False

        # Получаем тариф
        tariff = await tariff_service.get_tariff_by_id(payment_data.tariff_id)

        # Проверяем промокод
        PromoCodeValidator.validate(payment_data.promo_code)

        # Рассчитываем скидку
        discount, amount = DiscountCalculator.calculate(
            tariff.price,
            payment_data.promo_code,
        )

        # Рассчитываем график рассрочки
        schedule = None
        if payment_data.method == PaymentMethod.INSTALLMENT:
            schedule = InstallmentCalculator.calculate_schedule(
                amount,
                payment_data.installment_months,
            )

        payment = await self.create_payment(
            PaymentCreate(
                tariff_id=tariff.id,
                amount=amount,
                discount=discount,
                method=payment_data.method.value,
                email=payment_data.email,
                installment_months=payment_data.installment_months,
                schedule=schedule,
                idempotency_key=idempotency_key,
            ),
        )
        await self.payment_repo.session.commit()

        return payment, True

    async def process_webhook(self, webhook_data: "WebhookRequest") -> dict:
        """Обрабатывает вебхук от банка"""
        return await self.webhook_handler.process_bank_webhook(webhook_data)

    async def update_payment(
        self,
        payment_id: int,
        payment_data: PaymentUpdate,
    ) -> PaymentResponse:
        """Полное обновление платежа"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        updated = await self.payment_repo.update(payment, payment_data)
        return PaymentResponse.model_validate(updated)

    async def partial_update_payment(
        self,
        payment_id: int,
        payment_data: PaymentPartialUpdate,
    ) -> PaymentResponse:
        """Частичное обновление платежа"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        updated = await self.payment_repo.partial_update(payment, payment_data)
        await self.payment_repo.session.commit()
        return PaymentResponse.model_validate(updated)

    async def delete_payment(self, payment_id: int) -> None:
        """Удаляет платёж"""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise PaymentNotFoundError(payment_id)
        await self.payment_repo.delete(payment)
        await self.payment_repo.session.commit()
