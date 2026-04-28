from __future__ import annotations

import os

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> None:
    expected = os.getenv("API_KEY", "")
    if not expected:
        return  # API_KEY 未設定 = 開発モード（検証をスキップ）
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
