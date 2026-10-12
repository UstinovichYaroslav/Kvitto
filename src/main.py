from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from api import api_router
from core import settings
from infrastructure.database import db_helper
from infrastructure.repositories.tariff import TariffRepository
from infrastructure.services.tariff import TariffService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    # Startup
    async with db_helper.async_session_maker() as session:
        tariff_repo = TariffRepository(session)
        tariff_service = TariffService(tariff_repo)
        await tariff_service.init_default_tariffs()
    yield
    # Shutdown


app_main = FastAPI(
    title=settings.app.title,
    version=settings.app.version,
    description=settings.app.description,
    lifespan=lifespan,
)

app_main.include_router(api_router)


@app_main.get("/")
async def root() -> dict[str, str]:
    return {
        "message": "Kvitto Payment System",
        "docs": "http://localhost:8000/docs",
    }


if __name__ == "__main__":
    uvicorn.run(
        app="main:app_main",
        host=settings.run.host,
        port=settings.run.port,
    )
