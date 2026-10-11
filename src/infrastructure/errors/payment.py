from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from infrastructure.services.payment import PaymentStatus


class PaymentError(Exception):
    pass


class PaymentNotFoundError(PaymentError):
    def __init__(self, payment_id: int) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment with id {payment_id} not found")


class InvalidTransitionError(PaymentError):
    def __init__(self, src: "PaymentStatus", dst: "PaymentStatus") -> None:
        self.src = src
        self.dst = dst
        super().__init__(f"Invalid transition from {src} to {dst}")
