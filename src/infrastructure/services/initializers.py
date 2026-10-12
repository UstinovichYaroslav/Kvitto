from infrastructure.repositories.interface import ITariffRepository
from schemas.tariff import TariffCreate


class TariffInitializer:
    """Инициализатор дефолтных тарифов"""

    DEFAULT_TARIFFS = [
        TariffCreate(title="basic", price=990000),  # 9 900 ₽
        TariffCreate(title="standard", price=1990000),  # 19 900 ₽
        TariffCreate(title="premium", price=2990000),  # 29 900 ₽
    ]

    def __init__(self, tariff_repo: ITariffRepository) -> None:
        self.tariff_repo = tariff_repo

    async def init_default_tariffs(self) -> None:
        """Создаёт тарифы при старте, если их нет"""
        existing = await self.tariff_repo.get_all()
        if existing:
            return

        for tariff_data in self.DEFAULT_TARIFFS:
            await self.tariff_repo.create(tariff_data)

        await self.tariff_repo.session.commit()
