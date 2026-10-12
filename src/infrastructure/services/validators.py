class PromoCodeValidator:
    """Валидатор промокодов"""

    VALID_PROMO_CODE = "KVITTO10"

    @staticmethod
    def validate(promo_code: str | None) -> None:
        """Проверяет валидность промокода"""
        if promo_code and promo_code.upper() != PromoCodeValidator.VALID_PROMO_CODE:
            msg = "Invalid promo code"
            raise ValueError(msg)
