from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    """Application config"""

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    BASE_URL: str = "http://localhost:8000"
    CLIENT_URL: str = "http://localhost:3000"

    # App Settings
    PROJECT_NAME: str = "pizza-box api"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # Mail Settings
    MAIL_TOKEN_EXPIRE_SECONDS: int = 900
    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True

    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()  # type: ignore
