from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException, Security
from fastapi.security.api_key import APIKeyHeader

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
except ImportError:
    def get_remote_address(request: Any) -> str:
        return request.client.host if getattr(request, "client", None) else "testclient"

    class Limiter:  # type: ignore[no-redef]
        def __init__(self, key_func: Callable[[Any], str]) -> None:
            self.key_func = key_func

        def limit(self, _limit_value: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
                return fn

            return decorator

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
limiter = Limiter(key_func=get_remote_address)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> None:
    expected = os.getenv("API_KEY", "")
    if not expected:
        return  # API_KEY 未設定 = 開発モード（検証をスキップ）
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
