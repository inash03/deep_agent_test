"""Admin endpoints for seeding and refreshing demo data."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.infrastructure.db.session import get_db
from src.infrastructure.seed import reset_and_seed, seed_database

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.post("/seed", status_code=204)
def seed(db: Session = Depends(get_db)) -> None:
    """Idempotent seed — inserts initial data only if tables are empty."""
    seed_database(db)


@router.post("/refresh", status_code=204)
def refresh(db: Session = Depends(get_db)) -> None:
    """Reset all domain data to initial seed state (preserves triage history)."""
    reset_and_seed(db)
