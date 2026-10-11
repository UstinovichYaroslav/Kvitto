from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.errors import PaymentNotFoundError
from infrastructure.models.payment import PaymentMethod, PaymentStatus
from infrastructure.repositories.payment import PaymentRepository
from schemas.payment import (
    PaymentCreate,
    PaymentCreateRequest,
    PaymentPartialUpdate,
    PaymentResponse,
    PaymentUpdate,
    WebhookRequest,
    WebhookResponse,
)


class PaymentService:
    VALID_TRANSITIONS = {  # noqa: RUF012
        PaymentStatus.PENDING: [PaymentStatus.SUCCEEDED, PaymentStatus.FAILED],
        PaymentStatus.SUCCEEDED: [PaymentStatus.REFUNDED],
        PaymentStatus.FAILED: [],
        PaymentStatus.REFUNDED: [],
    }

    def __init__(self, session: AsyncSession) -> None:
        self.payment_repo = PaymentRepository(session)

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
        await self.payment_repo.session.commit()

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
        updated_payment = await self.payment_repo.update_status(payment, new_status)
        return PaymentResponse.model_validate(updated_payment)

    async def create_payment_with_validation(
        self,
        payment_data: PaymentCreateRequest,
        idempotency_key: str | None,
        tariff_service: "TariffService",  # noqa: F821
    ) -> PaymentResponse:
        """Создаёт платёж с валидацией"""
        # Проверка idempotency
        if idempotency_key:
            existing_payment = await self.get_payment_by_idempotency_key(
                idempotency_key,
            )
            if existing_payment:
                return existing_payment

        # Получаем тариф
        tariff = await tariff_service.get_tariff_by_id(payment_data.tariff_id)

        # Проверяем промокод
        if payment_data.promo_code and payment_data.promo_code.upper() != "KVITTO10":
            msg = "Invalid promo code"
            raise ValueError(msg)

        # Рассчитываем скидку
        discount, amount = self.calculate_discount(
            tariff.price,
            payment_data.promo_code,
        )

        # Рассчитываем график рассрочки
        schedule = None
        if payment_data.method == PaymentMethod.INSTALLMENT:
            schedule = self.calculate_installment_schedule(
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

        return payment

    async def process_webhook(self, webhook_data: WebhookRequest) -> dict:
        """Обрабатывает вебхук от банка"""
        payment = await self.get_payment_by_id(webhook_data.payment_id)

        if not self.validate_status_transition(payment.status, webhook_data.status):
            msg = "invalid_transition"
            raise ValueError(msg)

        await self.update_payment_status(webhook_data.payment_id, webhook_data.status)
        await self.payment_repo.session.commit()

        return WebhookResponse().model_dump()

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
        await self.payment_repo.session.commit()
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

    @staticmethod
    def calculate_discount(price: int, promo_code: str | None) -> tuple[int, int]:
        """
        Возвращает (discount, final_amount)
        promo_code KVITTO10 даёт -10% от цены тарифа, регистр не важен
        """
        if promo_code and promo_code.upper() == "KVITTO10":
            discount = price // 10
            final_amount = price - discount
            return discount, final_amount
        return 0, price

    @staticmethod
    def calculate_installment_schedule(amount: int, months: int) -> list[int]:
        """
        Рассчитывает график рассрочки.
        Сумма к оплате делится на срок в копейках.
        Лишние копейки — в первые платежи.
        """
        base_payment = amount // months
        remainder = amount % months

        schedule = []
        for i in range(months):
            if i < remainder:
                schedule.append(base_payment + 1)
            else:
                schedule.append(base_payment)

        return schedule

    @staticmethod
    def validate_status_transition(current_status: str, new_status: str) -> bool:
        """
        Проверяет допустимость перехода статуса.
        """
        current = PaymentStatus(current_status)
        new = PaymentStatus(new_status)

        allowed = PaymentService.VALID_TRANSITIONS.get(current, [])
        return new in allowed
