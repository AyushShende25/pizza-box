from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from app.core.config import settings
from app.auth.routes import auth_router
from app.core.exception_handlers import setup_exception_handlers
from app.menu.routes import menu_router
from app.uploads.routes import uploads_router
from app.cart.routes import cart_router
from app.address.routes import address_router
from app.orders.routes import orders_router
from app.payments.routes import payments_router
from app.notifications.events import start_event_listener
from app.notifications.routes import notifications_router
from app.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    listener_task = asyncio.create_task(start_event_listener())

    yield

    listener_task.cancel()
    try:
        await listener_task
    except asyncio.CancelledError:
        logger.info("Event listener stopped")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="rest api for pizza-box pizzeria",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CLIENT_URL, settings.ADMIN_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}")
app.include_router(menu_router, prefix=f"{settings.API_V1_STR}")
app.include_router(uploads_router, prefix=f"{settings.API_V1_STR}")
app.include_router(cart_router, prefix=f"{settings.API_V1_STR}")
app.include_router(address_router, prefix=f"{settings.API_V1_STR}")
app.include_router(orders_router, prefix=f"{settings.API_V1_STR}")
app.include_router(payments_router, prefix=f"{settings.API_V1_STR}")
app.include_router(notifications_router, prefix=f"{settings.API_V1_STR}")
