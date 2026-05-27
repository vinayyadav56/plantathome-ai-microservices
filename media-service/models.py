from pydantic import BaseModel
from typing import Optional
from enum import Enum


class OutputFormat(str, Enum):
    jpeg = "jpeg"
    png = "png"
    webp = "webp"


class ProcessImageRequest(BaseModel):
    image_base64: str
    output_format: OutputFormat = OutputFormat.webp
    max_width: Optional[int] = 1200
    max_height: Optional[int] = 1200
    quality: Optional[int] = 85
    remove_background: bool = False
    upload_to_s3: bool = False
    s3_key: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "image_base64": "<base64_string>",
                "output_format": "webp",
                "max_width": 800,
                "quality": 85,
                "remove_background": False,
                "upload_to_s3": True,
                "s3_key": "products/snake-plant.webp"
            }
        }


class ThumbnailRequest(BaseModel):
    image_base64: str
    sizes: list[int] = [150, 300, 600]
    output_format: OutputFormat = OutputFormat.webp
    upload_to_s3: bool = False
    s3_prefix: Optional[str] = None


class ThumbnailResult(BaseModel):
    size: int
    image_base64: Optional[str] = None
    s3_url: Optional[str] = None
    file_size_kb: float


class ProcessImageResponse(BaseModel):
    original_size_kb: float
    processed_size_kb: float
    compression_ratio: float
    width: int
    height: int
    format: str
    image_base64: Optional[str] = None
    s3_url: Optional[str] = None


class ThumbnailResponse(BaseModel):
    thumbnails: list[ThumbnailResult]
