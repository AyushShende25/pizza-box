import enum
from typing import Literal

from app.core.base_schema import BaseSchema


class PresignedUploadResponse(BaseSchema):
    upload_url: str
    file_url: str
    key: str


class UploadEntity(str, enum.Enum):
    PIZZA = "pizza"
    TOPPING = "topping"
    USER = "user"


ContentType = Literal[
    "image/jpeg",
    "image/png",
    "image/webp",
]


class UploadRequest(BaseSchema):
    entity_type: UploadEntity
    content_type: ContentType
