# Frontend Guide

Conventions for the Next.js App Router frontend and BFF. See
`docs/architecture.md` for how the frontend, BFF, and backend fit together.

## App Router Rules

- Use Next.js App Router conventions.
- Keep `layout.tsx` and route `page.tsx` files server components unless client
  behavior is required.
- Put interactive migrated screens in `frontend/src/screens/` as client
  components.
- Browser-side API calls must go to `/api/backend/*` (see `docs/security.md`).
- Do not expose backend secrets through `NEXT_PUBLIC_*`.
- Protected business pages must require Auth.js login. `/login` is public.
- Global font configuration lives in `frontend/src/app/layout.tsx` and
  `frontend/src/app/globals.css`.

## UI Language

- Business UI text should be English.
- The Home screen may provide English/Japanese switching.
- The Home screen default language must be English.
- Avoid mojibake. If text appears corrupted, rewrite it from the intended
  meaning instead of preserving broken bytes.

## Versioning

- `frontend/package.json` contains the display version.
- `frontend/src/version.ts` may show the short Vercel commit SHA.
- Bump the frontend version for user-visible frontend changes.
- Do not bump the frontend version for backend-only or docs-only changes unless
  release policy explicitly requires it.
</content>
