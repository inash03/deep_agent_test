"""FastAPI application entrypoint."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.logging_config import setup_logging
from src.presentation.router import router

load_dotenv()
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
