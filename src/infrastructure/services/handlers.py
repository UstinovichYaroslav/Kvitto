from infrastructure.errors import PaymentNotFoundError
from infrastructure.repositories.interface import IPaymentRepository
from schemas.payment import WebhookRequest, WebhookResponse


class WebhookHandler:
    """Обработчик вебхуков от банка"""

    def __init__(self, payment_repo: IPaymentRepository) -> None:
        self.payment_repo = payment_repo

    async def process_bank_webhook(self, webhook_data: WebhookRequest) -> dict:
        """Обрабатывает вебхук от банка"""
        from infrastructure.services.payment import PaymentStateMachine

        payment = await self.payment_repo.get_by_id(webhook_data.payment_id)
        if not payment:
            raise PaymentNotFoundError(webhook_data.payment_id)

        PaymentStateMachine.assert_transition(payment.status, webhook_data.status)

        await self.payment_repo.update_status(payment, webhook_data.status)

        return WebhookResponse().model_dump()
