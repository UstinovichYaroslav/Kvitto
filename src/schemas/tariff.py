from pydantic import BaseModel


class TariffResponse(BaseModel):
    id: int
    title: str
    price: int  # в копейках

    model_config = {"from_attributes": True}


class TariffCreate(BaseModel):
    title: str
    price: int  # в копейках


class TariffUpdate(BaseModel):
    title: str
    price: int  # в копейках


class TariffPartialUpdate(BaseModel):
    title: str | None = None
    price: int | None = None
