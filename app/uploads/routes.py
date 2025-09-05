from fastapi import APIRouter
from pydantic import BaseModel, field_validator
import uuid
import enum
from app.libs.bucket import client
from app.core.config import settings
from app.core.exceptions import AppException


uploads_router = APIRouter(prefix="/uploads", tags=["Uploads"])


class EntityType(str, enum.Enum):
    PIZZA = "pizza"
    TOPPING = "topping"
    USER = "user"


class UploadRequest(BaseModel):
    entity_type: EntityType
    content_type: str

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, v):
        allowed_types = ["image/jpeg", "image/png", "image/webp"]
        if v not in allowed_types:
            raise ValueError(f"Content type must be one of {allowed_types}")
        return v


ext_map = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@uploads_router.post("/presigned-url")
async def create_upload_url(body: UploadRequest):
    try:
        file_id = str(uuid.uuid4())
        ext = ext_map[body.content_type]
        key = f"{body.entity_type.value}/{file_id}.{ext}"

        signed_url = client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.BUCKET_NAME,
                "Key": key,
                "ContentType": body.content_type,
                "ACL": "public-read",
            },
            ExpiresIn=5 * 60,
        )

        file_url = (
            f"https://{settings.BUCKET_NAME}."
            f"{settings.BUCKET_REGION_NAME}.cdn.digitaloceanspaces.com/{key}"
        )

        return {"uploadUrl": signed_url, "fileUrl": file_url}
    except Exception as e:
        raise AppException(message="Failed to generate upload URL")
