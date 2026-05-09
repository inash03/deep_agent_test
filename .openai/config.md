# OpenAI/Codex Configuration Notes

Use `.codex.md` as the primary Codex-facing repository guide.

Important project defaults:

- Frontend uses Next.js App Router and Auth.js.
- Browser API calls go through the Next.js BFF at `/api/backend/*`.
- Backend runs on FastAPI + LangGraph on Cloud Run.
- Frontend deploys through Vercel Git Integration.
- Backend and MCP services deploy through GitHub Actions to Cloud Run.
- `README.md` is Japanese; all other project documentation should be English.
