import boto3
from botocore.client import Config
from app.core.config import settings


session = boto3.session.Session()

client = session.client(
    "s3",
    endpoint_url=settings.BUCKET_ENDPOINT_URL,
    config=Config(s3={"addressing_style": "virtual"}),
    region_name=settings.BUCKET_NAME,
    aws_access_key_id=settings.BUCKET_ACCESS_KEY_ID,
    aws_secret_access_key=settings.BUCKET_SECRET_ACCESS_KEY,
)
