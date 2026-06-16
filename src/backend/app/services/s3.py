import uuid

import boto3
from botocore.exceptions import ClientError

from app.core.config import settings

_client = None


def _s3():
    global _client
    if _client is None:
        _client = boto3.client("s3", region_name=settings.S3_REGION)
    return _client


def upload_proposal_content(proposal_id: uuid.UUID, content: str) -> str:
    """提案書テキストを S3 にアップロードし、オブジェクト URL を返す。"""
    if settings.APP_ENV == "demo":
        return f"https://demo-bucket.s3.ap-northeast-1.amazonaws.com/proposals/{proposal_id}/content.md"
    key = f"proposals/{proposal_id}/content.md"
    body = content.encode("utf-8")
    _s3().put_object(
        Bucket=settings.S3_BUCKET_PROPOSALS,
        Key=key,
        Body=body,
        ContentType="text/markdown; charset=utf-8",
    )
    return f"https://{settings.S3_BUCKET_PROPOSALS}.s3.{settings.S3_REGION}.amazonaws.com/{key}"


def generate_presigned_url(content_url: str, expires_in: int = 3600) -> str:
    """S3 オブジェクト URL から署名付き URL を生成する。"""
    # content_url から key を抽出
    prefix = f"https://{settings.S3_BUCKET_PROPOSALS}.s3.{settings.S3_REGION}.amazonaws.com/"
    key = content_url.removeprefix(prefix)
    try:
        return _s3().generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_PROPOSALS, "Key": key},
            ExpiresIn=expires_in,
        )
    except ClientError:
        return content_url
