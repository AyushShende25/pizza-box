from asgiref.sync import async_to_sync
from app.core.celery_app import celery_app
from app.libs.fastmail import FastMailService
from pydantic import EmailStr


@celery_app.task()
def send_mail_task(recipients: list[EmailStr], subject: str, body: str):
    mail_service = FastMailService()
    async_to_sync(mail_service.send_mail)(recipients, subject, body)
