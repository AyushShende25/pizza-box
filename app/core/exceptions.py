from fastapi import status


class AppException(Exception):
    """Base exception for application errors in pizza-box api"""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "Something went wrong."

    def __init__(
        self,
        message: str | None = None,
        error_code: str | None = None,
    ):
        if message:
            self.message = message
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)


class EntityNotFoundError(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "ENTITY_NOT_FOUND"
    message = "Entity not found in the database."


class ConflictError(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "ENTITY_ALREADY_EXISTS"
    message = "Entity already exists."


class BadRequestError(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "BAD_REQUEST"
    message = "Bad request"


class AuthenticationError(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "UNAUTHENTICATED"
    message = "Authentication failed"


class AuthorizationError(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "UNAUTHORIZED_ACCESS"
    message = "Access denied"
