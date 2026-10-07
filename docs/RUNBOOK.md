# Operations runbook

## Fresh database

1. Configure `DATABASE_URL` for PostgreSQL/Neon.
2. Run `python manage.py migrate`.
3. Run `python manage.py seed_neon_demo`.
4. Run `python manage.py check` and the backend test suite.
5. Start Django, then start the Next.js frontend with its API URL configured.

## Rollback

Deploy the previous application revision. Database migrations are forward-safe additions; if a schema rollback is required, take a Neon branch or backup first and migrate the `operations` and `accounts` apps to their previous migration identifiers. Never delete production assignments, SLA events, or audit events as a rollback shortcut.

## Troubleshooting

- `SLA_POLICY_MISSING`: seed or publish an effective policy matching the work-order priority.
- `SCHEDULE_CONFLICT`: refresh the dispatch board and choose another lane or window.
- Empty dispatch board: verify the role has `dispatch.view` and the tenant has active technicians.
- Preferences not applying: confirm the authenticated request reaches `/api/v1/accessibility-preferences/` and reload the shell.
