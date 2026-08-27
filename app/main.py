from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.core.model_registry as _models  # noqa: F401
from app.address.routes import address_router
from app.auth.routes import auth_router
from app.cart.routes import cart_router
from app.core.config import settings
from app.core.exception_handlers import setup_exception_handlers
from app.menu.routes import menu_router
from app.notifications.listener import notification_listener
from app.notifications.pubsub import pubsub_service
from app.notifications.routes import notifications_router
from app.orders.routes import orders_router
from app.payments.routes import payments_router
from app.store_config.routes import store_config_router
from app.uploads.routes import uploads_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    await notification_listener.start()

    yield

    # Shutdown
    await notification_listener.stop()
    await pubsub_service.close()


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
app.include_router(store_config_router, prefix=f"{settings.API_V1_STR}")
