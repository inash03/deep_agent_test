"""FastAPI application entrypoint."""

from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI

from src.presentation.router import router

load_dotenv()

app = FastAPI(
    title="STP Exception Triage Agent",
    description=(
        "LangGraph ReAct agent that investigates STP failures, diagnoses the "
        "root cause, and (with operator approval) registers missing SSIs."
    ),
    version="0.1.0",
)

app.include_router(router)
