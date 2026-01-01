import boto3
from app.core.config import settings


session = boto3.session.Session()

client = session.client(
    "s3",
    region_name=settings.BUCKET_REGION_NAME,
    aws_access_key_id=settings.BUCKET_ACCESS_KEY_ID,
    aws_secret_access_key=settings.BUCKET_SECRET_ACCESS_KEY,
)
