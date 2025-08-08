from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Uuid, TIMESTAMP, func, Boolean
from datetime import datetime
import uuid
import enum
from app.core.base import Base


class UserRole(enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(length=255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, title='{self.email}', author='{self.first_name}')>"
