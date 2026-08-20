import uuid

from boto3.exceptions import Boto3Error
from fastapi import APIRouter

from app.core.config import settings
from app.core.exceptions import AppException
from app.libs.s3 import s3_client
from app.utils.logger import logger

from .schema import ContentType, PresignedUploadResponse, UploadRequest

uploads_router = APIRouter(prefix="/uploads", tags=["Uploads"])


EXTENSION_BY_CONTENT_TYPE: dict[ContentType, str] = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@uploads_router.post("/presigned-url", response_model=PresignedUploadResponse)
async def create_upload_url(body: UploadRequest):
    file_id = str(uuid.uuid4())

    extension = EXTENSION_BY_CONTENT_TYPE[body.content_type]

    key = f"{body.entity_type.value}/{file_id}.{extension}"

    try:
        upload_url = s3_client.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": settings.BUCKET_NAME,
                "Key": key,
                "ContentType": body.content_type,
            },
            ExpiresIn=5 * 60,
        )
    except Boto3Error:
        logger.exception("Failed to generate S3 presigned URL")
        raise AppException(
            error_code="UPLOAD_URL_GENERATION_FAILED",
            message="Failed to generate upload URL",
        )

    return PresignedUploadResponse(
        upload_url=upload_url,
        file_url=f"{settings.BUCKET_CUSTOM_DOMAIN}/{key}",
        key=key,
    )
