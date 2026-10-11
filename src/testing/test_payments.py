import uuid

import pytest
from httpx import AsyncClient
from starlette import status

from main import app_main
from testing.conftest import PaymentChecker


@pytest.mark.asyncio
@pytest.mark.parametrize("months", [3, 6, 12])
async def test_installment_schedule(
    payment_checker: PaymentChecker,
    tariff_id: int,
    months: int,
) -> None:
    """Сумма графика рассрочки равна сумме к оплате, длина = числу месяцев."""
    price = 100_000

    result = await payment_checker.create(
        tariff_id,
        email=f"installment_{months}@example.com",
        method="installment",
        installment_months=months,
    )

    assert result.raw["method"] == "installment"
    assert result.raw["installment_months"] == months
    assert result.schedule is not None
    assert (
        len(result.schedule) == months
    ), f"expected {months} payments, got {len(result.schedule)}"
    assert (
        sum(result.schedule) == result.amount
    ), f"schedule sum {sum(result.schedule)} != amount {result.amount}"
    assert result.amount == price


@pytest.mark.asyncio
async def test_promo_code_discount(
    async_client: AsyncClient,
    tariff_id: int,
    payment_checker: PaymentChecker,
) -> None:
    """Тест промокода с скидкой и без."""
    base_price = 100_000
    promo = "KVITTO10"
    discount = 10_000

    # Без промокода — скидки нет
    await payment_checker.expect_discount(
        tariff_id,
        base_price=base_price,
        promo_code=None,
        expected_discount=0,
        email="no_promo@example.com",
    )

    # С промокодом в верхнем регистре
    await payment_checker.expect_discount(
        tariff_id,
        base_price=base_price,
        promo_code=promo,
        expected_discount=discount,
        email="promo_upper@example.com",
    )

    # С промокодом в нижнем регистре — регистронезависимо
    await payment_checker.expect_discount(
        tariff_id,
        base_price=base_price,
        promo_code=promo.lower(),
        expected_discount=discount,
        email="promo_lower@example.com",
    )

    # Неверный промокод — 422
    response = await async_client.post(
        payment_checker.url,
        json={
            "tariff_id": tariff_id,
            "email": "invalid@example.com",
            "method": "card",
            "promo_code": "INVALID",
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.asyncio
async def test_idempotency_key(
    payment_checker: PaymentChecker,
    tariff_id: int,
) -> None:
    """Повторный запрос с тем же idempotency_key не создаёт второй платёж."""
    uniq = uuid.uuid4().hex[:8]
    key = f"test-idempotency-{uniq}"
    email = f"idem-{uniq}@example.com"

    first = await payment_checker.create(tariff_id, email, idempotency_key=key)
    second = await payment_checker.create(tariff_id, email, idempotency_key=key)

    assert second.id == first.id
    assert second.amount == first.amount
    assert second.raw == first.raw

    all_payments = await payment_checker.list_all()
    same_email = [p for p in all_payments if p["email"] == email]
    assert (
        len(same_email) == 1
    ), f"expected 1 payment with email {email}, got {len(same_email)}"


@pytest.mark.asyncio
async def test_non_existent_payment_404(async_client: AsyncClient) -> None:
    """Все операции над несуществующим платежом → 404."""
    non_existent_id = 999_999

    # GET
    response = await async_client.get(
        url=app_main.url_path_for(
            "get_payment",
            payment_id=non_existent_id,
        ),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text

    # PUT
    response = await async_client.put(
        url=app_main.url_path_for("update_payment", payment_id=non_existent_id),
        json={
            "status": "succeeded",
            "amount": 100_000,
            "discount": 0,
            "method": "card",
            "email": "x@example.com",
            "installment_months": 0,
            "schedule": [],
            "idempotency_key": "x",
        },
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text

    # PATCH
    response = await async_client.patch(
        url=app_main.url_path_for(
            "partial_update_payment",
            payment_id=non_existent_id,
        ),
        json={"status": "succeeded"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text

    # DELETE
    response = await async_client.delete(
        url=app_main.url_path_for(
            "delete_payment",
            payment_id=non_existent_id,
        ),
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND, response.text


@pytest.mark.asyncio
async def test_invalid_status_transition(
    payment_checker: PaymentChecker,
    tariff_id: int,
) -> None:
    """Запрещённый переход статуса → 409 и статус не меняется."""
    payment = await payment_checker.create(tariff_id, "transition@example.com")
    assert payment.status == "pending"

    # pending → succeeded разрешён
    response = await payment_checker.webhook(payment.id, "succeeded")
    assert response.status_code == status.HTTP_200_OK, response.text

    # Проверяем, что статус поменялся
    updated = await payment_checker.get(payment.id)
    assert updated["status"] == "succeeded"

    # succeeded → pending запрещён → 409
    response = await payment_checker.webhook(payment.id, "pending")
    assert response.status_code == status.HTTP_409_CONFLICT, response.text
    body = response.json()
    assert body.get("error") == "invalid_transition"

    # Статус не изменился
    after = await payment_checker.get(payment.id)
    assert after["status"] == "succeeded"
