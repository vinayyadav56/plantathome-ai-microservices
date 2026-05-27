import os
import boto3
from botocore.exceptions import ClientError

AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "plantathome-images")

_s3_client = None


def get_s3():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            region_name=AWS_REGION,
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
    return _s3_client


def upload_bytes(data: bytes, key: str, content_type: str = "image/webp") -> str:
    s3 = get_s3()
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=data,
        ContentType=content_type,
        ACL="public-read",
        CacheControl="max-age=31536000",
    )
    return f"https://{BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{key}"


def is_configured() -> bool:
    return bool(os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY"))
