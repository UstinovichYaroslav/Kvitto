import random
import string
from collections.abc import AsyncGenerator
from dataclasses import dataclass

import httpx
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from starlette import status

from infrastructure.database import db_helper
from main import app_main
from schemas.tariff import TariffCreate


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app_main)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@dataclass
class PaymentResult:
    id: int
    amount: int
    discount: int
    status: str
    schedule: list[int] | None
    raw: dict


class PaymentChecker:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client
        self.url = app_main.url_path_for("create_payment")

    async def create(  # noqa: PLR0913
        self,
        tariff_id: int,
        email: str,
        *,
        promo_code: str | None = None,
        method: str = "card",
        installment_months: int | None = None,
        idempotency_key: str | None = None,
        expect_status: int = status.HTTP_201_CREATED,
    ) -> PaymentResult:
        payload: dict = {
            "tariff_id": tariff_id,
            "email": email,
            "method": method,
        }
        if promo_code is not None:
            payload["promo_code"] = promo_code
        if installment_months is not None:
            payload["installment_months"] = installment_months

        headers = {}
        if idempotency_key is not None:
            headers["Idempotency-Key"] = idempotency_key

        response = await self.client.post(self.url, json=payload, headers=headers)
        assert response.status_code == expect_status, response.text
        data = response.json()
        return PaymentResult(
            id=data["id"],
            amount=data["amount"],
            discount=data["discount"],
            status=data["status"],
            schedule=data.get("schedule"),
            raw=data,
        )

    async def get(self, payment_id: int) -> dict:
        url = app_main.url_path_for("get_payment", payment_id=payment_id)
        response = await self.client.get(url)
        assert response.status_code == status.HTTP_200_OK, response.text
        return response.json()

    async def list_all(self) -> list[dict]:
        url = app_main.url_path_for("get_payments")
        response = await self.client.get(url)
        assert response.status_code == status.HTTP_200_OK, response.text
        return response.json()

    async def webhook(self, payment_id: int, new_status: str) -> httpx.Response:
        url = app_main.url_path_for("webhook_bank")
        return await self.client.post(
            url,
            json={"payment_id": payment_id, "status": new_status},
        )

    async def expect_discount(
        self,
        tariff_id: int,
        *,
        base_price: int,
        promo_code: str | None,
        expected_discount: int,
        email: str,
    ) -> PaymentResult:
        result = await self.create(tariff_id, email, promo_code=promo_code)
        assert result.discount == expected_discount, (
            f"promo={promo_code!r}: expected discount {expected_discount}, "
            f"got {result.discount}"
        )
        assert result.amount == base_price - expected_discount, (
            f"promo={promo_code!r}: expected amount "
            f"{base_price - expected_discount}, got {result.amount}"
        )
        return result


@pytest_asyncio.fixture
async def payment_checker(async_client: AsyncClient) -> PaymentChecker:
    return PaymentChecker(async_client)


@pytest_asyncio.fixture
async def tariff_id(async_client: AsyncClient) -> AsyncGenerator[int]:
    url = app_main.url_path_for("create_tariff")
    tariff = TariffCreate(
        title="".join(random.choices(string.ascii_letters, k=8)),  # noqa: S311
        price=100_000,
    )
    response = await async_client.post(url=url, json=tariff.model_dump(mode="json"))
    assert response.status_code == status.HTTP_201_CREATED, response.text
    yield response.json()["id"]


TABLES_TO_TRUNCATE = ("payments", "tariffs")


@pytest_asyncio.fixture(autouse=True, scope="function")
async def clean_db() -> AsyncGenerator[None]:
    """Очищает все таблицы перед каждым тестом."""
    async with db_helper.engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE "
                + ", ".join(TABLES_TO_TRUNCATE)
                + " RESTART IDENTITY CASCADE",
            ),
        )
    yield
    async with db_helper.engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE TABLE "
                + ", ".join(TABLES_TO_TRUNCATE)
                + " RESTART IDENTITY CASCADE",
            ),
        )
