"""FastAPI application entrypoint."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.logging_config import setup_logging
from src.infrastructure.secrets import load_secrets
from src.presentation.router import router

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
