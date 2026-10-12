

class DiscountCalculator:
    """Калькулятор скидок"""

    PROMO_CODE = "KVITTO10"
    DISCOUNT_PERCENT = 10

    @staticmethod
    def calculate(price: int, promo_code: str | None) -> tuple[int, int]:
        """
        Возвращает (discount, final_amount)
        promo_code KVITTO10 даёт -10% от цены тарифа, регистр не важен
        """
        if promo_code and promo_code.upper() == DiscountCalculator.PROMO_CODE:
            discount = price // DiscountCalculator.DISCOUNT_PERCENT
            final_amount = price - discount
            return discount, final_amount
        return 0, price


class InstallmentCalculator:
    """Калькулятор графика рассрочки"""

    @staticmethod
    def calculate_schedule(amount: int, months: int) -> list[int]:
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
