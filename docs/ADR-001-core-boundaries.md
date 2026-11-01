# ADR-001: Keep OIE Core Framework-Independent

Status: Accepted

## Decision

OIE Core will be a pure Python library with no FastAPI, ORM, database, queue, cloud, or LLM dependency.

## Rationale

This keeps the intellectual core deterministic, portable, easy to test, and reusable by PulseOps or future products.

## Consequences

Adapters and infrastructure will depend on OIE Core, never the reverse.
