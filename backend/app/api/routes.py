from fastapi import APIRouter
from app.api import health
from app.api import auth
from app.settings import settings

router = APIRouter()

# Include all routers
if settings.ENVIRONMENT == "development":
    router.include_router(health.router, prefix="/health", tags=["Health"])

router.include_router(auth.router, prefix="/auth", tags=["Auth"])
