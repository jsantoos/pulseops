# PulseOps M6.1D — Hardening

This milestone hardens the authenticated multi-tenant MVP before the ML layer.

## Delivered

- Tenant-scoped audit log with Alembic migration `0003_audit_log`.
- Audit events for organization creation, dataset upload, CSV-bundle import, analysis and outcome recording.
- Admin/owner audit API: `GET /v1/audit-events`.
- Expired sessions are revoked when detected; logout deletes the server-side session and clears the frontend tenant selection.
- Mutating web requests keep the application marker and reject explicit browser origins outside the configured frontend allowlist.
- RBAC regression test proving a `viewer` cannot upload datasets.
- Cross-tenant regression protection retained.
- FastAPI/Pydantic structured errors are rendered as readable frontend messages instead of `[object Object]`.
- First-access password has client-side minimum length consistent with the API.
- Primary CTA contrast is enforced by the semantic `.button-primary` class; `Ver análise` is explicitly white on the dark-blue background.

## Database upgrade

```bash
uv run --package pulseops-api alembic upgrade head
```

Expected Alembic head: `0003_audit_log`.

## Validation

```bash
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run pytest
uv run ruff check .
uv run mypy apps/api/src packages/oie_core/src
```

Frontend:

```bash
cd apps/web
npm install
npm run typecheck
npm run lint
npm run build
npm run dev
```

## Security scope

This is MVP hardening, not a completed production security program. Before public production deployment we still need TLS-only cookies, secret management, rate limiting, password-reset/invitation flows, security headers, deployment-level CSRF review, backup/restore testing, and a formal threat model.
