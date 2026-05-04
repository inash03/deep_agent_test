"""RAG service — embedding generation, chunk storage, and semantic retrieval.

Uses OpenAI text-embedding-3-small (1536 dimensions) via langchain-openai.
If OPENAI_API_KEY or DATABASE_URL is not set, all operations are silently no-ops
so triage runs continue normally without RAG.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.domain.entities import TriageResult

_logger = logging.getLogger("stp_triage.rag_service")


class RagService:
    def __init__(self) -> None:
        self._embedder = None

    def _is_available(self) -> bool:
        return bool(os.environ.get("OPENAI_API_KEY") and os.environ.get("DATABASE_URL"))

    def _get_embedder(self):
        if self._embedder is None:
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return None
            from langchain_openai import OpenAIEmbeddings
            self._embedder = OpenAIEmbeddings(
                model="text-embedding-3-small",
                api_key=api_key,
            )
        return self._embedder

    def search_similar(
        self,
        query: str,
        agent_type: str | None = None,
        k: int = 3,
    ) -> list[str]:
        """Return content strings of the k most similar RAG chunks.

        Returns an empty list when RAG is unavailable or on any error.
        """
        if not self._is_available():
            return []
        embedder = self._get_embedder()
        if embedder is None:
            return []
        try:
            embedding = embedder.embed_query(query)
            from src.infrastructure.db.session import make_session
            from src.infrastructure.db.rag_repository import RagRepository
            db = make_session()
            try:
                chunks = RagRepository(db).search_similar(
                    embedding, agent_type=agent_type, k=k
                )
                return [c.content for c in chunks]
            finally:
                db.close()
        except Exception as exc:
            _logger.warning("rag_service.search_similar failed: %s", exc)
            return []

    def store_chunk(
        self,
        content: str,
        source_type: str,
        agent_type: str | None = None,
        source_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Embed and persist a single RAG chunk."""
        if not self._is_available():
            return
        embedder = self._get_embedder()
        if embedder is None:
            return
        try:
            embedding = embedder.embed_documents([content])[0]
            from src.infrastructure.db.session import make_session
            from src.infrastructure.db.rag_repository import RagRepository
            db = make_session()
            try:
                RagRepository(db).upsert(
                    content=content,
                    embedding=embedding,
                    source_type=source_type,
                    source_id=source_id,
                    agent_type=agent_type,
                    metadata=metadata,
                )
                db.commit()
            finally:
                db.close()
        except Exception as exc:
            _logger.warning("rag_service.store_chunk failed: %s", exc)

    def store_triage_result(
        self,
        result: "TriageResult",
        agent_type: str,
        error_message: str = "",
        failed_rules: list[str] | None = None,
        triage_path: str = "",
    ) -> None:
        """Store a completed triage result as a RAG chunk for future retrieval."""
        if result.diagnosis is None:
            return
        lines = [
            f"[{agent_type.upper()} TRIAGE CASE]",
        ]
        if error_message:
            lines.append(f"Error: {error_message}")
        if failed_rules:
            lines.append(f"Failed rules: {failed_rules}")
        if triage_path:
            lines.append(f"Triage path: {triage_path}")
        lines += [
            f"Root cause: {result.root_cause.value if result.root_cause else 'UNKNOWN'}",
            f"Diagnosis: {result.diagnosis}",
        ]
        if result.recommended_action:
            lines.append(f"Recommended action: {result.recommended_action}")
        lines.append(f"Action taken: {result.action_taken}")

        content = "\n".join(lines)
        self.store_chunk(
            content=content,
            source_type="triage_case",
            source_id=result.run_id,
            agent_type=agent_type,
            metadata={
                "trade_id": result.trade_id,
                "root_cause": result.root_cause.value if result.root_cause else None,
                "triage_path": triage_path,
            },
        )


# Module-level singleton — shared across tools and use cases
_rag_service = RagService()
