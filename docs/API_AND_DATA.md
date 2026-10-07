# API and data guide

## Scheduling and SLA

- `GET|POST /api/v1/organizations/{slug}/operations/sla-policies/`
- `POST /api/v1/organizations/{slug}/operations/work-orders/{id}/apply-sla/`
- `GET|POST /api/v1/organizations/{slug}/operations/dispatch/`

SLA deadlines are derived from a versioned policy and business calendar. Applying a policy persists the selected policy, deadlines and an append-only clock event so results can be reproduced. Assignment creation locks the selected technician and work order, rechecks overlap inside the transaction and returns `SCHEDULE_CONFLICT` without writing when occupied.

## Accessibility

- `GET|PATCH /api/v1/accessibility-preferences/`

Preferences belong to the authenticated user and only influence presentation. They never change tenant business records.

## Seed strategy

`seed_neon_demo` is the canonical idempotent expanded dataset command for a fresh PostgreSQL/Neon database. It invokes the three foundational seed commands first and then adds scheduling, SLA, preferences and higher-volume operational records.
