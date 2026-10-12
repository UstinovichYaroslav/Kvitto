from pydantic import BaseModel, Field


class TariffResponse(BaseModel):
    id: int
    title: str
    price: int  # в копейках

    model_config = {"from_attributes": True}


class TariffCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    price: int = Field(gt=0)  # в копейках


class TariffUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    price: int = Field(gt=0)  # в копейках


class TariffPartialUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=100)
    price: int | None = Field(None, gt=0)
