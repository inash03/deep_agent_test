"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from src.infrastructure.logging_config import setup_logging
from src.infrastructure.secrets import load_secrets
from src.presentation.dependencies import limiter
from src.presentation.router import router
from src.presentation.routers.counterparties import router as counterparties_router
from src.presentation.routers.reference_data import router as reference_data_router
from src.presentation.routers.seed import router as seed_router
from src.presentation.routers.ssis import router as ssis_router
from src.presentation.routers.stp_exceptions import router as stp_exceptions_router
from src.presentation.routers.bo_triage import router as bo_triage_router
from src.presentation.routers.fo_triage import router as fo_triage_router
from src.presentation.routers.trade_events import router as trade_events_router
from src.presentation.routers.rules import router as rules_router
from src.presentation.routers.settings import router as settings_router
from src.presentation.routers.trades import router as trades_router

# 順序が重要:
#   1. load_dotenv()  → .env から SECRET_BACKEND / GCP_PROJECT_ID などを読む
#   2. load_secrets() → SECRET_BACKEND に応じてシークレットを os.environ に注入
#   3. setup_logging() / app 初期化 → ANTHROPIC_API_KEY 等が使える状態になっている
load_dotenv()
load_secrets()
setup_logging()

app = FastAPI(
    title="STP Exception Triage Agent",
    description=(
        "LangGraph ReAct agent that investigates STP failures, diagnoses the "
        "root cause, and (with operator approval) registers missing SSIs."
    ),
    version="0.1.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)

_logger = logging.getLogger("stp_triage.main")


@app.exception_handler(Exception)
async def _unhandled_exc_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler so unhandled 500s still carry CORS headers.

    FastAPI's CORSMiddleware wraps the response sender but exceptions that
    escape without being caught bypass that wrapper. We re-add CORS headers
    here manually so browser clients can read the error body.
    """
    _logger.error("Unhandled exception on %s: %s", request.url.path, exc, exc_info=True)
    origin = request.headers.get("origin", "")
    headers: dict[str, str] = {}
    if origin and (origin in _cors_origins or "*" in _cors_origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Vary"] = "Origin"
    return JSONResponse(
        status_code=500,
        content={"detail": f"{type(exc).__name__}: {exc}"},
        headers=headers or None,
    )


app.include_router(router)
app.include_router(trades_router)
app.include_router(counterparties_router)
app.include_router(stp_exceptions_router)
app.include_router(ssis_router)
app.include_router(reference_data_router)
app.include_router(seed_router)
app.include_router(rules_router)
app.include_router(settings_router)
app.include_router(bo_triage_router)
app.include_router(fo_triage_router)
app.include_router(trade_events_router)
