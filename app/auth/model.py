import enum
import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, Enum, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.address.model import Address
from app.core.base import Base
from app.notifications.model import Notification


class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        unique=True,
    )
    password_hash: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    first_name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.USER,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    addresses: Mapped[list["Address"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"
