# PulseOps M6.1B/C — Authentication + Multi-tenancy

The tenant UUID is no longer configured in the frontend. Authentication and organization isolation are enforced server-side.

## One-time upgrade

If an older milestone is still running, stop its containers first to release port 5432:

```bash
sudo docker compose down
```

From this milestone forward the Compose project has the stable name `pulseops`, so future milestone folders will reuse the same development volume.

Start the new milestone:

```bash
sudo docker compose up -d
uv sync --all-packages --all-groups
uv run --package pulseops-api alembic upgrade head
uv run --package pulseops-api uvicorn pulseops_api.main:app --reload
```

Frontend:

```bash
cd apps/web
cp .env.local.example .env.local
npm install
npm run dev
```

Use `http://localhost:3000` and `http://localhost:8000` consistently so the HttpOnly session cookie remains same-site.

## First access

Open:

```text
http://localhost:3000/login
```

If there are no users, the frontend displays the first-owner setup.

- If the database already contains exactly one organization, that organization is reused automatically.
- If the database is new, enter the organization name as well.
- Bootstrap is disabled after the first user is created and is unavailable in production.

After login the frontend obtains memberships from `/v1/auth/me`. No `NEXT_PUBLIC_PULSEOPS_ORGANIZATION_ID` exists anymore.

## Validation

```bash
curl http://localhost:8000/health
uv run pytest -q
```

Expected test result for this milestone: `26 passed`.

Migration validation:

```bash
sudo docker compose exec postgres \
  psql -U pulseops -d pulseops \
  -c "SELECT version_num FROM alembic_version;"
```

Expected head:

```text
0002_auth_multitenancy
```

New tables:

```text
users
user_sessions
organization_memberships
```
