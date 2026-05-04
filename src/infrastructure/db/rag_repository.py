"""Repository for RAG chunks (semantic vector store operations)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from src.infrastructure.db.models import RagChunk


class RagRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search_similar(
        self,
        embedding: list[float],
        agent_type: str | None = None,
        k: int = 3,
    ) -> list[RagChunk]:
        """Return k most similar chunks sorted by cosine distance."""
        query = self._db.query(RagChunk).filter(RagChunk.embedding.isnot(None))
        if agent_type:
            query = query.filter(RagChunk.agent_type == agent_type)
        return (
            query
            .order_by(RagChunk.embedding.cosine_distance(embedding))
            .limit(k)
            .all()
        )

    def upsert(
        self,
        content: str,
        embedding: list[float],
        source_type: str,
        source_id: str | None = None,
        agent_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RagChunk:
        """Insert a new chunk, or update content/embedding if source_id already exists."""
        if source_id:
            existing = (
                self._db.query(RagChunk)
                .filter(RagChunk.source_id == source_id)
                .first()
            )
            if existing is not None:
                existing.content = content
                existing.embedding = embedding
                existing.rag_metadata = metadata
                return existing

        chunk = RagChunk(
            id=uuid.uuid4(),
            source_type=source_type,
            source_id=source_id,
            agent_type=agent_type,
            content=content,
            rag_metadata=metadata,
            embedding=embedding,
            created_at=datetime.now(timezone.utc),
        )
        self._db.add(chunk)
        return chunk
