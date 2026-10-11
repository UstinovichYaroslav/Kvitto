class PaymentNotFoundError(Exception):
    def __init__(self, payment_id: int) -> None:
        self.payment_id = payment_id
        super().__init__(f"Payment with id {payment_id} not found")
