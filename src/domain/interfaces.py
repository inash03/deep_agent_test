"""Domain interfaces (abstract base classes).

Defines contracts that the Infrastructure layer must implement.
The Presentation layer depends only on these interfaces — never on
concrete infrastructure classes directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities import STPFailure, TriageResult


class ITriageUseCase(ABC):
    """Contract for the STP Exception Triage use case.

    Two-phase execution to support Human-in-the-Loop:

    1. start(failure) — runs the ReAct loop until completion or HITL interrupt.
       Returns TriageResult with:
         - status=COMPLETED  → diagnosis is ready, no action required
         - status=PENDING_APPROVAL → agent wants to register SSI; run_id is set

    2. resume(run_id, approved) — resumes a PENDING_APPROVAL run.
       approved=True  → agent executes the action and completes
       approved=False → agent skips the action and completes
    """

    @abstractmethod
    def start(self, failure: STPFailure) -> TriageResult:
        """Start a new triage run for the given STP failure."""
        ...

    @abstractmethod
    def resume(self, run_id: str, *, approved: bool) -> TriageResult:
        """Resume a paused triage run after HITL decision."""
        ...
