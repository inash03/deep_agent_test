"""Persistent LangGraph checkpointer backed by PostgreSQL.

Uses PostgresSaver (langgraph-checkpoint-postgres) with a psycopg3 ConnectionPool
so that HITL state survives Cloud Run instance restarts and load-balancing.

Falls back to MemorySaver when DATABASE_URL is not set (unit tests / local dev).
"""

from __future__ import annotations

import logging
import os
from typing import Any

_logger = logging.getLogger("stp_triage.checkpointer")
_checkpointer: Any = None


def get_checkpointer() -> Any:
    """Return the shared checkpointer instance (created once per process)."""
    global _checkpointer
    if _checkpointer is not None:
        return _checkpointer

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        from langgraph.checkpoint.memory import MemorySaver
        _checkpointer = MemorySaver()
        _logger.warning(
            "DATABASE_URL not set — using MemorySaver; "
            "HITL state will not survive process restarts"
        )
        return _checkpointer

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        from psycopg_pool import ConnectionPool

        pool = ConnectionPool(
            conninfo=db_url,
            max_size=5,
            # prepare_threshold=0 required for Neon / pgBouncer (no prepared statements)
            kwargs={"autocommit": True, "prepare_threshold": 0},
        )
        _checkpointer = PostgresSaver(pool)
        _checkpointer.setup()  # idempotent — creates tables on first run
        _logger.info("PostgresSaver initialised (persistent checkpointer)")
    except Exception as exc:
        from langgraph.checkpoint.memory import MemorySaver
        _logger.error(
            "PostgresSaver init failed, falling back to MemorySaver: %s", exc
        )
        _checkpointer = MemorySaver()

    return _checkpointer
