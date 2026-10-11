class TariffError(Exception):
    pass


class TariffNotFoundError(TariffError):
    def __init__(self, tariff_id: int) -> None:
        self.tariff_id = tariff_id
        super().__init__(f"Tariff with id {tariff_id} not found")


class TariffInUseError(TariffError):
    def __init__(self, tariff_id: int) -> None:
        self.tariff_id = tariff_id
        super().__init__(f"Tariff with id {tariff_id} is in use")
