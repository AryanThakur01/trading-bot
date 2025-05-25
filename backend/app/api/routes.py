from fastapi import APIRouter
from app.api import health

router = APIRouter()

# Include all routers
router.include_router(health.router, prefix="/health", tags=["Health"])
