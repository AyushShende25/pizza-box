from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from app.core.config import settings
from app.utils.logger import logger


class FastMailService:
    def __init__(self):
        self.fastmail = FastMail(
            config=ConnectionConfig(
                MAIL_USERNAME=settings.MAIL_USERNAME,
                MAIL_PASSWORD=settings.MAIL_PASSWORD,
                MAIL_FROM=settings.MAIL_FROM,
                MAIL_PORT=settings.MAIL_PORT,
                MAIL_SERVER=settings.MAIL_SERVER,
                MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
                MAIL_STARTTLS=settings.MAIL_STARTTLS,
                MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
                USE_CREDENTIALS=settings.USE_CREDENTIALS,
                VALIDATE_CERTS=settings.VALIDATE_CERTS,
            )
        )

    async def send_mail(self, recipients: list[EmailStr], subject: str, body: str):
        try:
            await self.fastmail.send_message(
                MessageSchema(
                    subject=subject,
                    recipients=recipients,
                    body=body,
                    subtype=MessageType.html,
                )
            )
        except Exception as e:
            logger.exception("Email sending failed")
            raise RuntimeError(f"Email sending failed: {e}")
