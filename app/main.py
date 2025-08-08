from fastapi import FastAPI
from app.core.config import settings
from app.auth.routes import auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="rest api for pizza-box pizzeria",
)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}")
