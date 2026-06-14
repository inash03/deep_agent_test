# ADR-0008: tasks.md is a pure scratchpad; retire progress.md and tasks_done.md

- **Status:** Accepted
- **Date:** 2026-06-14
- **Deciders:** architect, maintainers
- **Supersedes:** none (extends ADR-0002)
- **Superseded by:** none

## Context

ADR-0002 moved the source of truth for tasks to GitHub Issues / Projects and
demoted `docs/tasks.md` to an in-branch working note, but the repository kept
three overlapping Markdown trackers: `docs/tasks.md` (still holding a shared
backlog), `docs/progress.md` (a chronological log), and `docs/tasks_done.md` (a
completed-task archive).

These duplicate state that GitHub already owns. A backlog in `tasks.md` conflicts
under concurrent edits and has no owner/priority/audit trail; the progress log
and done-archive are an audit trail that the Issue/PR timeline and git history
already provide. Maintaining them by hand is exactly the document rot the
AI-driven process warns against, and they drift out of date (e.g. stale "Phase 1"
rollout status).

## Decision

We will treat `docs/tasks.md` as a **pure scratchpad** — ephemeral working
memory for the current branch/agent session — and **retire** `docs/progress.md`
and `docs/tasks_done.md`.

- Task state, ownership, priority, and history live in GitHub Issues / Projects
  and the PR/commit timeline.
- `docs/tasks.md` holds only the current session's plan, findings, and next step.
  It is not shared, cross-session state and may be overwritten or cleared freely.
- Backlog items that previously lived in `tasks.md` are migrated to Issues
  (drafts staged in `docs/issue-drafts.md` until filed, then that file is
  deleted).

## Consequences

- Easier: a single source of truth for task state; no hand-maintained logs to
  rot; clearer that durable knowledge belongs in `docs/` and mutable state in
  Issues.
- Harder: progress narrative is no longer in one Markdown file. It must be read
  from Issue/PR timelines and git history. This is an accepted trade-off; those
  systems already provide ownership, audit, and concurrency that Markdown cannot.
- Follow-up: file the `docs/issue-drafts.md` drafts as Issues, then delete that
  file. Update docs that referenced `progress.md`/`tasks_done.md`.

## Alternatives considered

- **Keep all three Markdown files.** Rejected: duplicates GitHub state, conflicts
  under concurrent edits, and rots — the original motivation for ADR-0002.
- **Keep `progress.md` as a human-readable changelog.** Rejected: the PR/commit
  timeline and release notes already serve this; a parallel hand-edited log
  drifts and adds maintenance with no unique source of truth.
- **Auto-generate `progress.md` from Issues/PRs.** Rejected for now as
  unnecessary tooling; git and the GitHub timeline are already queryable.
</content>
