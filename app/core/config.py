from pydantic_settings import SettingsConfigDict, BaseSettings
from pydantic import SecretStr


class Settings(BaseSettings):
    """Application config"""

    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    BASE_URL: str = "http://localhost:8000"
    CLIENT_URL: str = "http://localhost:5173"
    ADMIN_URL: str = "http://localhost:3000"

    # App Settings
    PROJECT_NAME: str = "pizza-box api"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    APP_ENV: str

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

    # Bucket storage settings
    BUCKET_ACCESS_KEY_ID: str
    BUCKET_SECRET_ACCESS_KEY: str
    BUCKET_ENDPOINT_URL: str
    BUCKET_CUSTOM_DOMAIN: str
    BUCKET_NAME: str
    BUCKET_REGION_NAME: str

    # Razorpay Keys
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str

    model_config = SettingsConfigDict(
        env_file=".env.local",
        extra="ignore",
    )


settings = Settings()  # type: ignore
