from typing import Annotated
from fastapi import Depends
from app.libs.fastmail import FastMailService


def get_mail_service() -> FastMailService:
    """Dependency provider for MailService."""
    return FastMailService()


FastMailDep = Annotated[FastMailService, Depends(get_mail_service)]
