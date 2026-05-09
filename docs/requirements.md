# Requirements

## Project Overview

**Name:** `deep_agent_test`

**Purpose:** Demonstrate an STP exception triage workflow for securities
operations using rule-based checks, LangGraph agents, Human-in-the-Loop
approval, and a Next.js business UI.

## Goals

1. Model FO/BO trade validation workflows with explicit states.
2. Use deterministic rule checks for common validation failures.
3. Use LangGraph agents for investigation, explanation, and remediation plans.
4. Require human approval before write actions that change operational data.
5. Keep backend API keys and LLM credentials out of the browser by using a
   Next.js BFF.
6. Support Vercel Preview/Production deployments for the frontend and Cloud Run
   deployments for backend services.
7. Keep the codebase understandable for learning Next.js, Auth.js, FastAPI, and
   LangGraph together.

## Functional Requirements

| ID | Requirement | Status |
| --- | --- | --- |
| FR-01 | Create and list trades | Implemented |
| FR-02 | Manage counterparties, SSI, reference data, and STP exceptions | Implemented |
| FR-03 | Run FO rule checks and update trade workflow status | Implemented |
| FR-04 | Run BO rule checks and update trade workflow status | Implemented |
| FR-05 | Start and resume FO triage with HITL approval | Implemented |
| FR-06 | Start and resume BO triage with HITL approval | Implemented |
| FR-07 | Persist triage runs, steps, diagnoses, and root causes | Implemented |
| FR-08 | Manage amend/cancel trade events and trade versions | Implemented |
| FR-09 | Show triage history | Implemented |
| FR-10 | Show rules, settings, and LLM cost dashboards | Implemented |
| FR-11 | Use MCP/external data lookup for market data use cases | Implemented |
| FR-12 | Support Auth.js login with a single administrator account | Implemented |
| FR-13 | Proxy browser API calls through the Next.js BFF | Implemented |
| FR-14 | Hide `BACKEND_API_KEY` from browser JavaScript | Implemented |
| FR-15 | Deploy frontend through Vercel Git Integration | Implemented |
| FR-16 | Deploy backend and MCP services through GitHub Actions to Cloud Run | Implemented |
| FR-17 | Provide English UI text except for the optional Japanese Home view | Implemented |
| FR-18 | Display frontend version and short commit SHA | Implemented |

## Non-Functional Requirements

| Category | Requirement |
| --- | --- |
| Security | Browser code must not contain backend API keys or LLM provider keys. |
| Security | Auth.js must protect business pages and BFF API routes. |
| Security | FastAPI protected endpoints must validate `X-API-Key` when configured. |
| Security | Secrets must live in environment variables, Vercel secrets, GitHub secrets, or Cloud Run secrets. |
| Auditability | Triage decisions, HITL approvals, and tool calls should be persisted where relevant. |
| Maintainability | Backend code should keep presentation, domain, and infrastructure concerns separated. |
| Maintainability | Frontend routes should follow Next.js App Router conventions. |
| Testability | Unit tests should avoid real LLM calls unless explicitly marked as integration tests. |
| Observability | Backend should log agent steps, decisions, and cost information in structured form. |
| Deployability | Frontend and backend deployment paths should be independent and not require a fixed order for backward-compatible changes. |

## Authentication Requirements

- `/login` is public.
- Business pages under the protected layout require an Auth.js session.
- `/api/backend/*` requires an Auth.js session before forwarding to FastAPI.
- Initial authentication uses `APP_USERNAME` and `APP_PASSWORD_HASH`.
- `APP_PASSWORD_HASH` must be a bcrypt hash, not a plaintext password.
- `AUTH_SECRET` is required in production and is used by Auth.js for session/JWT
  protection.

## API Requirements

Browser code must call the BFF using `/api/backend/*`. The BFF forwards to the
FastAPI `/api/v1/*` contract.

Important backend API areas:

- Trades: list, create, detail, FO/BO checks, FO/BO triage, trade events
- Counterparties: list, detail, update
- SSI: list, detail, update
- STP exceptions: list, create, update, start triage
- Reference data: list
- Triage history: list
- Rules: list
- Settings: read/update
- Cost: summary and recent logs

## Frontend Language Requirements

- Default UI copy is English.
- The Home screen may offer English/Japanese display switching.
- The Home screen default language is English.
- Documentation language:
  - `README.md` is Japanese.
  - Files under `docs/` are English.
  - Agent instruction files such as `CLAUDE.md` and `.codex.md` are English.

## Out of Scope

- Multi-user account management and role-based authorization.
- Moving LLM/agent execution into Next.js.
- Replacing FastAPI with Next.js API routes.
- Direct browser access to Cloud Run APIs in production.
- Full enterprise identity provider integration.
