# Security Guide

Security rules for this repository. These are non-negotiable guardrails.

## Secrets

- Never commit `.env` or real secret values.
- Store secrets in Vercel, GitHub Environments, Cloud Run secrets, or local
  `.env` files.

## Keys and their roles

- `AUTH_SECRET` is for Auth.js session/JWT protection only.
- `BACKEND_API_KEY` is used by the Next.js BFF when calling FastAPI.
- FastAPI uses `API_KEY` to validate protected backend requests.

## Boundaries

- Browser code must call `/api/backend/*`; the backend API key is attached only
  server-side by the BFF. Never expose it through `NEXT_PUBLIC_*`.
- Do not let agents execute arbitrary shell commands.
- Keep HITL approval explicit for write actions that change operational data.
</content>
