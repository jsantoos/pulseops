# M5 — Application Foundation

## Goal
Expose OIE through a thin application layer without duplicating intelligence logic.

## First vertical slice
1. Create organization.
2. Upload and validate a canonical operational JSON dataset.
3. Persist immutable uploaded payload + SHA-256.
4. Execute OIE analysis.
5. Persist structured opportunities/evidence.
6. Query opportunities by organization.
7. Record an outcome for later learning.

## Boundaries
- OIE remains framework-independent.
- API performs orchestration only.
- PostgreSQL is the production database; SQLite is used for isolated tests.
- No patient identity is required by the M5 capacity flow.
- Raw uploaded data is persisted only for MVP reproducibility; production retention/encryption policy must be decided before real patient-derived datasets.
