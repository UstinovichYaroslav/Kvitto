from sqlalchemy import select

from infrastructure.models.payment import Payment
from infrastructure.repositories.interface import IPaymentRepository
from schemas.payment import PaymentCreate, PaymentPartialUpdate, PaymentUpdate


class PaymentRepository(IPaymentRepository):
    async def create(self, payment_data: PaymentCreate) -> Payment:
        payment = Payment(**payment_data.model_dump())
        self.session.add(payment)
        await self.session.commit()
        return payment

    async def get_all(self) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, payment_id: int) -> Payment | None:
        return await self.session.get(Payment, payment_id)

    async def get_by_idempotency_key(self, key: str) -> Payment | None:
        stmt = select(Payment).where(Payment.idempotency_key == key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update(self, payment: Payment, payment_data: PaymentUpdate) -> Payment:
        """Полное обновление платежа"""
        for key, value in payment_data.model_dump().items():
            setattr(payment, key, value)
        await self.session.commit()
        return payment

    async def partial_update(
        self,
        payment: Payment,
        payment_data: PaymentPartialUpdate,
    ) -> Payment:
        """Частичное обновление платежа"""
        for key, value in payment_data.model_dump(exclude_unset=True).items():
            setattr(payment, key, value)
        await self.session.commit()
        return payment

    async def delete(self, payment: Payment) -> None:
        """Удаление платежа"""
        await self.session.delete(payment)
        await self.session.commit()

    async def update_status(self, payment: Payment, new_status: str) -> Payment:
        payment.status = new_status
        await self.session.commit()
        return payment
