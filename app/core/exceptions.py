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


# Auth specific errors
class UserNotFoundError(EntityNotFoundError):
    error_code = "USER_NOT_FOUND"
    message = "User does not exist."


class UserAlreadyExistsError(ConflictError):
    error_code = "USER_ALREADY_EXISTS"
    message = "User with that email already exists."


class InvalidCredentialsError(AuthenticationError):
    error_code = "INVALID_CREDENTIALS"
    message = "Incorrect email or password."


class InvalidTokenError(BadRequestError):
    error_code = "INVALID_TOKEN"
    message = "Invalid or expired token."


class UnverifiedAccountError(AuthenticationError):
    error_code = "ACCOUNT_NOT_VERIFIED"
    message = "Please verify your account first"


class AlreadyVerifiedError(BadRequestError):
    error_code = "ALREADY_VERIFIED"
    message = "User is already verified"


class InvalidRefreshTokenError(AuthenticationError):
    error_code = "INVALID_REFRESH_TOKEN"
    message = "Invalid refresh token"


# Pizza Errors
class PizzaAlreadyExistsError(ConflictError):
    error_code = "PIZZA_ALREADY_EXISTS"
    message = "Pizza with that name already exists."


class PizzaNotFoundError(EntityNotFoundError):
    error_code = "PIZZA_NOT_FOUND"
    message = "Pizza does not exist."


class ToppingAlreadyExistsError(ConflictError):
    error_code = "TOPPING_ALREADY_EXISTS"
    message = "Topping with that name already exists."


class ToppingNotFoundError(EntityNotFoundError):
    error_code = "TOPPING_NOT_FOUND"
    message = "Topping does not exist."


class SizeAlreadyExistsError(ConflictError):
    error_code = "SIZE_ALREADY_EXISTS"
    message = "Size with that name already exists."


class SizeNotFoundError(EntityNotFoundError):
    error_code = "SIZE_NOT_FOUND"
    message = "Size does not exist."


class CrustAlreadyExistsError(ConflictError):
    error_code = "CRUST_ALREADY_EXISTS"
    message = "Crust with that name already exists."


class CrustNotFoundError(EntityNotFoundError):
    error_code = "CRUST_NOT_FOUND"
    message = "Crust does not exist."


# Cart Errors


class CartNotFoundError(EntityNotFoundError):
    error_code = "CART_NOT_FOUND"
    message = "Cart does not exist."


class CartItemNotFoundError(EntityNotFoundError):
    error_code = "CART_ITEM_NOT_FOUND"
    message = "Cart item does not exist."


class MaxAddressesExceededError(BadRequestError):
    error_code = "MAX_ADDRESSES_PER_USER_EXCEEDED"
    message = "User already has too many addresses"
