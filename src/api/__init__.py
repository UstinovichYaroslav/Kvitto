from fastapi import APIRouter

from api.api_v1 import payments, tariffs, webhooks
from core import settings

api_router = APIRouter(prefix=settings.api.prefix)

api_router.include_router(tariffs.router)
api_router.include_router(payments.router)
api_router.include_router(webhooks.router)
