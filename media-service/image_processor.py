import base64
import io
import uuid
from PIL import Image
from models import (
    ProcessImageRequest, ProcessImageResponse,
    ThumbnailRequest, ThumbnailResponse, ThumbnailResult, OutputFormat,
)
from s3_service import upload_bytes, is_configured

CONTENT_TYPES = {
    OutputFormat.jpeg: "image/jpeg",
    OutputFormat.png:  "image/png",
    OutputFormat.webp: "image/webp",
}

PIL_FORMATS = {
    OutputFormat.jpeg: "JPEG",
    OutputFormat.png:  "PNG",
    OutputFormat.webp: "WEBP",
}


def _decode(b64: str) -> bytes:
    return base64.b64decode(b64)


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def _resize(img: Image.Image, max_w: int | None, max_h: int | None) -> Image.Image:
    if not max_w and not max_h:
        return img
    img.thumbnail((max_w or 9999, max_h or 9999), Image.LANCZOS)
    return img


def _save(img: Image.Image, fmt: OutputFormat, quality: int) -> bytes:
    buf = io.BytesIO()
    save_kwargs = {"format": PIL_FORMATS[fmt]}
    if fmt in (OutputFormat.jpeg, OutputFormat.webp):
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    if fmt == OutputFormat.jpeg and img.mode == "RGBA":
        img = img.convert("RGB")
    img.save(buf, **save_kwargs)
    return buf.getvalue()


def _remove_bg(img: Image.Image) -> Image.Image:
    from rembg import remove
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    result = remove(buf.getvalue())
    return Image.open(io.BytesIO(result)).convert("RGBA")


def process_image(request: ProcessImageRequest) -> ProcessImageResponse:
    raw = _decode(request.image_base64)
    original_kb = len(raw) / 1024

    img = Image.open(io.BytesIO(raw))

    if request.remove_background:
        img = _remove_bg(img)

    img = _resize(img, request.max_width, request.max_height)
    processed = _save(img, request.output_format, request.quality or 85)
    processed_kb = len(processed) / 1024

    s3_url = None
    if request.upload_to_s3 and is_configured():
        key = request.s3_key or f"processed/{uuid.uuid4()}.{request.output_format}"
        s3_url = upload_bytes(processed, key, CONTENT_TYPES[request.output_format])

    return ProcessImageResponse(
        original_size_kb=round(original_kb, 2),
        processed_size_kb=round(processed_kb, 2),
        compression_ratio=round(original_kb / processed_kb, 2) if processed_kb > 0 else 1.0,
        width=img.width,
        height=img.height,
        format=request.output_format,
        image_base64=_encode(processed) if not s3_url else None,
        s3_url=s3_url,
    )


def generate_thumbnails(request: ThumbnailRequest) -> ThumbnailResponse:
    raw = _decode(request.image_base64)
    results = []

    for size in request.sizes:
        img = Image.open(io.BytesIO(raw)).copy()
        img.thumbnail((size, size), Image.LANCZOS)
        thumb_bytes = _save(img, request.output_format, 85)
        thumb_kb = len(thumb_bytes) / 1024

        s3_url = None
        if request.upload_to_s3 and is_configured():
            key = f"{request.s3_prefix or 'thumbnails'}/{size}.{request.output_format}"
            s3_url = upload_bytes(thumb_bytes, key, CONTENT_TYPES[request.output_format])

        results.append(ThumbnailResult(
            size=size,
            image_base64=_encode(thumb_bytes) if not s3_url else None,
            s3_url=s3_url,
            file_size_kb=round(thumb_kb, 2),
        ))

    return ThumbnailResponse(thumbnails=results)
