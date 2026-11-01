# M6 — PulseOps Web

## Scope

The first web vertical slice consumes the existing PulseOps API and implements:

- Opportunity Inbox, sorted by OIE score.
- Opportunity detail with evidence and recommendations.
- Outcome recording (accept/dismiss).
- PulseOps Connect CSV bundle upload and automatic analysis.
- Runtime response validation with Zod.
- Server-state caching and invalidation with TanStack Query.

## Boundary

The web app does not reproduce OIE business logic. Financial impact, confidence, scoring, evidence and recommendations remain backend/OIE responsibilities.

## Local configuration

Copy `apps/web/.env.local.example` to `apps/web/.env.local` and set the organization ID created by the backend.
