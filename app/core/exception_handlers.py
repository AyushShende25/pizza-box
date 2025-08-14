from fastapi.responses import JSONResponse
from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.utils.logger import logger
from app.core.exceptions import AppException


async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        f"unhandled error {repr(exc)} - URL:  {request.url.path}",
        extra={
            "exception_type": type(exc).__name__,
            "url": str(request.url),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "INTERNAL_SERVER_ERROR",
            "message": "Something went wrong, please try again later",
        },
    )


async def app_exception_handler(request: Request, exc: AppException):
    """Handle custom application exceptions."""
    logger.warning(
        f"Application error: [{exc.error_code}] - {exc.message} - URL: {request.url.path}",
        extra={
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "url": str(request.url),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        f"Validation error - URL: {request.url.path}",
        extra={
            "errors": exc.errors(),
            "url": str(request.url),
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "message": "Validation failed",
            "error": "VALIDATION_ERROR",
            "details": {"errors": exc.errors()},
        },
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle standard HTTP exceptions."""
    logger.warning(
        f"HTTP error {exc.status_code}: {exc.detail} - URL: {request.url.path}",
        extra={
            "status_code": exc.status_code,
            "detail": exc.detail,
            "url": str(request.url),
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "error": f"HTTP_{exc.status_code}",
        },
    )


def setup_exception_handlers(app):
    """Setup all exception handlers."""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)
