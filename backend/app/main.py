from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Trading Bot Platform")
app.include_router(router, prefix="/api")
