# KaziLayer project context

KaziLayer is an adaptive service-operations control centre for organisations coordinating requests, sites, assets, technicians, work orders, evidence, and audit history. Its primary users are organisation owners, dispatchers, technicians, customer contacts, and auditors.

The authoritative product requirements are KL-F-01 through KL-F-24 in the KaziLayer portfolio brief. Backend policy and domain state are authoritative. The frontend owns accessible presentation and projects versioned contract metadata through reusable field renderers, recipes, slots, actions, and page blocks.

## Current stack

- Frontend: Next.js 16 App Router, React 19, TypeScript 5, Tailwind CSS 4, pnpm.
- Backend: Python 3.13, Django 6.1, Channels, PostgreSQL/Redis-ready dependencies, uv.
- Planned local services: PostgreSQL, Redis or Valkey, and S3-compatible object storage.

## Canonical commands

- Frontend development: `cd frontend && pnpm dev`
- Frontend lint: `cd frontend && pnpm lint`
- Frontend production build: `cd frontend && pnpm build`
- Backend checks: `cd backend && uv run python manage.py check`
- Backend tests: `cd backend && uv run pytest`

## Bootstrap status

The repository currently has framework scaffolds and brand assets, but the backend contract generator, domain apps, PostgreSQL/Redis configuration, Compose stack, CI workflow, and end-to-end contract generation loop are not implemented yet. The frontend design kernel is being established without inventing backend permissions or domain rules.
