import os
from fastapi import HTTPException, Header
from typing import Optional

SERVICE_API_KEY = os.getenv("SERVICE_API_KEY", "")


def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    if SERVICE_API_KEY and x_api_key != SERVICE_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Key header")
