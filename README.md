# KaziLayer

KaziLayer is a multi-tenant service-operations control centre for organisations coordinating requests, dispatch, field work, evidence and audit history. It uses Adaptive Convergence: Django owns business truth and publishes tenant-aware policy and data contracts; the Next.js interface projects those facts through reusable fields, recipes and page blocks.

## Current product slice

- **KL-F-01 Tenant identity:** organisations, tenant settings, logos and memberships with strict organisation scoping.
- **KL-F-02 Authentication and sessions:** email-first accounts, secure cookie sessions, password reset tokens, session revocation, encrypted TOTP MFA and avatar uploads.
- **KL-F-03 Role policy:** versioned tenant role policies, resource scopes, allowed actions, deterministic priority and backend enforcement.
- **KL-F-11 Saved views:** user and tenant-scoped filters, sorts, columns, density, dashboard selections and one default per module.
- **KL-F-22 User feedback:** consent-aware route, role and viewport context with triage status.
- **KL-F-07 Request intake:** idempotent service requests, urgency, location and preferred windows.
- **KL-F-13 Comments and mentions:** visibility-aware collaboration with sanitised restricted rich text and derived plain text.
- **KL-F-14 File evidence:** storage-backed uploads, integrity hashes, scan state, visibility and opaque object keys.
- **KL-F-16 Search:** tenant-authorised search projections with bounded queries and resource filters.
- **KL-F-19 Imports and exports:** asynchronous job records, validation counts and frozen export manifests.
- **KL-F-20 Audit ledger:** immutable, append-only events with redacted before/after summaries.
- **KL-F-08 Work lifecycle:** guarded state transitions, evidence requirements, rich instructions and completion summaries.
- **KL-F-17 Notifications:** preferences, restricted-rich-text templates, deduplication and tenant delivery records.
- Tenant-aware profile, people, role policy, saved views and organisation settings pages.
- A responsive Swiss technical, modular Bento and blueprint visual system.

## Architecture

```text
backend/                 Django API, domain models, policy and seed data
frontend/                Next.js App Router and contract-oriented UI kernel
contract/                Versioned generated contract artefacts
design/                  Design-token sources and references
docs/                    Project context and visual direction
```

Tenant, authentication and permission facts are evaluated on the backend. Uploaded avatars and organisation logos use Django's storage API: local media storage is the development default and an S3-compatible backend can be selected through configuration.

## Local development

```powershell
cd backend
uv sync --dev
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_kazilayer
.\.venv\Scripts\python.exe manage.py seed_operations
.\.venv\Scripts\python.exe manage.py runserver 8000
```

In a second terminal:

```powershell
cd frontend
pnpm install
pnpm dev
```

Open `http://localhost:3000/login`. Next.js proxies `/api/*` to `http://127.0.0.1:8000` by default.

For another frontend hostname or port, add its complete origin to the comma-separated
`DJANGO_CSRF_TRUSTED_ORIGINS` environment variable. Production deployments must set
this to their HTTPS application origin and configure `DJANGO_ALLOWED_HOSTS` separately.

## Seeded demonstration data

The idempotent seed creates **Meridian Field Services** (`meridian-field-services`) and **Rift Valley Facilities** (`rift-valley-facilities`). Each receives organisation owner, dispatcher, technician, customer contact and auditor policies. The same identities belong to both tenants to demonstrate tenant-specific memberships.

| Account | Display name | Role | Password |
|---|---|---|---|
| `owner@demo.kazilayer.test` | Tuki Gichovi | Organisation owner | `KaziLayerDemo!2026` |
| `dispatcher@demo.kazilayer.test` | Amina Kamau | Dispatcher | `KaziLayerDemo!2026` |
| `technician@demo.kazilayer.test` | Brian Mwangi | Technician | `KaziLayerDemo!2026` |
| `customer@demo.kazilayer.test` | Linet Wanjiku | Customer contact | `KaziLayerDemo!2026` |
| `auditor@demo.kazilayer.test` | Omar Hassan | Auditor | `KaziLayerDemo!2026` |

The seed also creates an SLA-risk work-order view for the dispatcher and an active-team view for the owner in each tenant. These credentials are for local development only.

`seed_operations` adds, per tenant, one customer request, one scheduled work order with transition history, one sanitised rich-text comment, one evidence metadata record, one feedback item, one search document, one completed import, one completed export, one immutable audit event, notification preferences and four deduplicated in-app notifications. It also extends each role with only the operational actions appropriate to that identity.

## Operational feature URLs

Replace `{tenant}` with `meridian-field-services` or `rift-valley-facilities`.

| Feature | URL |
|---|---|
| User feedback | `/{tenant}/feedback` |
| Request intake | `/{tenant}/requests` |
| Comments | `/{tenant}/comments` |
| File evidence | `/{tenant}/files` |
| Search | `/{tenant}/search` |
| Imports and exports | `/{tenant}/data-jobs` |
| Audit ledger | `/{tenant}/audit` |
| Work lifecycle | `/{tenant}/work-orders` |
| Notifications | `/{tenant}/notifications` |

Rich-text HTML is never accepted as trusted browser output. The backend allow-lists supported elements and attributes and derives plain-text projections for search, export, accessibility and notification snippets.

## Simulated build timeline

| Phase | Simulated period | Outcome |
|---|---|---|
| Foundation | Week 1 | Repository rules, stack bootstrap, tokens and visual direction |
| Identity | Week 2 | KL-F-01 tenants, memberships and media fields |
| Security | Week 3 | KL-F-02 sessions, password reset, revocation, MFA and profile |
| Policy | Week 4 | KL-F-03 role registry and allowed-action projection |
| Personalisation | Week 5 | KL-F-11 saved views and settings surfaces |
| Convergence gate | Week 6 | Seed data, tests and responsive review |
| Operational expansion | Weeks 7-10 | Requests, work lifecycle, evidence, audit and notifications |
| Advanced operations | Weeks 11-14 | Dashboards, realtime, integrations, SLA and dispatch |

The dates are planning simulations, not a record of elapsed development time. Screenshots will be added after the functional tenant flows stabilise.

## Verification

```powershell
cd backend
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe -m pytest

cd ..\frontend
pnpm lint
pnpm build
```
