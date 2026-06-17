"""Architecture fitness functions (pytest-archon).

ArchUnit-style, pytest-native complement to the declarative import-linter
contracts in `.importlinter`. These enforce Clean Architecture dependency rules
as machine checks so the boundary stays a gate, not a convention.

Marked `architecture` and excluded from the default suite (advisory rollout);
run with `uv run pytest -m architecture`. Rationale and staged rollout to
blocking: docs/governance/automated-gates.md and ADR-0009.

`skip_type_checking=True` ignores `if TYPE_CHECKING:` imports, mirroring the
single accepted-debt edge recorded in `.importlinter`
(`src.domain.check_rules -> src.infrastructure.db.models`).
"""

import pytest
from pytest_archon import archrule

pytestmark = pytest.mark.architecture


def test_domain_does_not_depend_on_outer_layers() -> None:
    (
        archrule("domain independence")
        .match("src.domain*")
        .should_not_import("src.infrastructure*", "src.presentation*")
        .check("src", skip_type_checking=True)
    )


def test_domain_is_framework_free() -> None:
    (
        archrule("domain purity")
        .match("src.domain*")
        .should_not_import("fastapi*", "sqlalchemy*", "langgraph*", "langchain*")
        .check("src", skip_type_checking=True)
    )
