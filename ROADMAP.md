# PulseOps / OIE — Development Roadmap

> **Status:** Planned work | **Maintainer:** Project owner | **Last updated:** November 2026
>
> This roadmap outlines intended future engineering tasks. It does not represent completed work or promise delivery dates. Estimates are approximate and should be revised as the project evolves.

## Product direction

PulseOps is an operational management application for diagnostic-clinic workflows. Its OIE (Operational Intelligence Engine) core supports explainable operational findings, including capacity and cancellation-related opportunities. The repository also documents predictive and model-evaluation components.

The next proposed development phase prioritizes conventional application engineering: robust ingestion, API contracts, operational workflows, user experience, automated testing, and documentation. **The tasks listed here do not include training, fine-tuning, evaluating, or benchmarking ML models.**

> **BYOP eligibility note:** The repository's existing ML-related components and healthcare domain may require explicit approval under the program's restrictions. Working only on the tasks below does not by itself establish eligibility. Public demo data must be synthetic and must not include real patient or customer information.

## Planned work at a glance

| ID | Priority | Workstream | Estimated effort | Status |
|---|---|---|---:|---|
| PO-01 | P0 | CSV ingestion validation and error reporting | 20 h | Planned |
| PO-02 | P0 | Dataset and opportunity API contract hardening | 18 h | Planned |
| PO-03 | P0 | Backend integration tests and fixtures | 26 h | Planned |
| PO-04 | P0 | Opportunity lifecycle and decision workflow reliability | 22 h | Planned |
| PO-05 | P1 | Dashboard filtering and operational navigation | 22 h | Planned |
| PO-06 | P1 | Business explainability and financial presentation UX | 18 h | Planned |
| PO-07 | P1 | Authorization, data isolation, and safe logging | 24 h | Planned |
| PO-08 | P1 | CI, local environment, and migration reliability | 18 h | Planned |
| PO-09 | P2 | Observability and API diagnostics | 16 h | Planned |
| PO-10 | P2 | Documentation and synthetic demo walkthrough | 16 h | Planned |
| | | **Total planned independent development** | **200 h** | |

These are planning estimates, not logged hours or guaranteed commitments.

## Phase 1 — Data and workflow reliability (86 h)

### PO-01 — CSV ingestion validation and error reporting (20 h)
**Goal:** Make operational data uploads easier to validate, troubleshoot, and correct.

- [ ] Define clear schemas for equipment, availability, appointments, and executions.
- [ ] Improve missing-column, invalid-type, and invalid-date messages.
- [ ] Report row-level validation errors without exposing sensitive content.
- [ ] Add checks for duplicate and inconsistent records.
- [ ] Expand tests with synthetic valid and invalid CSV bundles.

**Done when:** Invalid uploads fail predictably with actionable, non-sensitive error messages.

### PO-02 — Dataset and opportunity API contract hardening (18 h)
**Goal:** Make the REST API consistent and straightforward for client applications.

- [ ] Review response schemas, pagination, and error codes.
- [ ] Validate organization and dataset identifiers.
- [ ] Define consistent status transitions and response shapes.
- [ ] Improve OpenAPI descriptions and example payloads.
- [ ] Add negative-case tests for malformed and missing resources.

**Done when:** Core API contracts are documented and tested.

### PO-03 — Backend integration tests and fixtures (26 h)
**Goal:** Reduce regressions across ingestion, persistence, and operational workflows.

- [ ] Add repeatable PostgreSQL-backed test fixtures.
- [ ] Test dataset creation, validation, and analysis endpoints.
- [ ] Verify transaction and rollback behavior.
- [ ] Cover organization-scoped data access.
- [ ] Document test setup and cleanup commands.

**Done when:** Core API workflows can be exercised in automated integration tests.

### PO-04 — Opportunity lifecycle and decision workflow reliability (22 h)
**Goal:** Keep opportunity states and decisions consistent.

- [ ] Document allowed opportunity status transitions.
- [ ] Prevent duplicate or conflicting decisions.
- [ ] Improve handling of closed and measured opportunities.
- [ ] Add audit-friendly timestamps and state-change tests.
- [ ] Improve error states in the web interface.

**Done when:** Tested workflows prevent invalid state changes and show clear user feedback.

## Phase 2 — User experience and application safeguards (82 h)

### PO-05 — Dashboard filtering and operational navigation (22 h)
- [ ] Improve filtering by status, category, and operational period.
- [ ] Add clear empty, loading, and failure states.
- [ ] Improve navigation between summary and opportunity details.
- [ ] Review responsive layouts and keyboard interaction.
- [ ] Add component tests for key filters and actions.

**Done when:** Users can navigate and filter operational opportunities reliably.

### PO-06 — Business explainability and financial presentation UX (18 h)
- [ ] Standardize labels for observed, calculated, and estimated values.
- [ ] Clarify assumptions and limitations in opportunity details.
- [ ] Review BRL, percentage, and duration formatting.
- [ ] Improve presentation of evidence and calculation steps.
- [ ] Test the display of missing or partial financial data.

**Done when:** Business users can distinguish evidence from estimates in the interface.

### PO-07 — Authorization, data isolation, and safe logging (24 h)
- [ ] Review organization-scoped access rules across endpoints.
- [ ] Add tests for cross-organization access denial.
- [ ] Review secret handling and environment configuration.
- [ ] Prevent sensitive payloads from appearing in logs.
- [ ] Document development-only use of synthetic data.

**Done when:** Organization boundaries and safe logging behavior are covered by tests.

### PO-08 — CI, local environment, and migration reliability (18 h)
- [ ] Add or refine GitHub Actions for lint, tests, and builds.
- [ ] Validate clean-checkout setup and Docker Compose instructions.
- [ ] Document database initialization and Alembic migrations.
- [ ] Add checks for environment configuration errors.
- [ ] Ensure example files do not contain real credentials.

**Done when:** The documented development workflow is reproducible from a fresh clone.

## Phase 3 — Operations and onboarding (32 h)

### PO-09 — Observability and API diagnostics (16 h)
- [ ] Improve structured application logs.
- [ ] Add request correlation identifiers where useful.
- [ ] Distinguish validation, application, and infrastructure errors.
- [ ] Document health checks and troubleshooting procedures.
- [ ] Add tests for stable error response formats.

**Done when:** Common operational failures can be diagnosed without disclosing sensitive data.

### PO-10 — Documentation and synthetic demo walkthrough (16 h)
- [ ] Align README with implemented milestones and current structure.
- [ ] Document API and web startup commands.
- [ ] Add architecture diagrams and representative screenshots.
- [ ] Provide a fully synthetic end-to-end demo walkthrough.
- [ ] Create contributor guidance and issue templates.

**Done when:** An external reviewer can install, run, and understand the product without real clinic data.

## Suggested GitHub Issues

Create one issue for each roadmap ID (`PO-01` through `PO-10`). Each issue should link back to this roadmap and include acceptance criteria, scope, and a rough estimate. Suggested labels: `backend`, `frontend`, `testing`, `documentation`, `security`, `priority:P0`.

## Delivery and tracking

- Keep tasks marked as planned until implementation is complete.
- Link actual pull requests and commits to the corresponding issues.
- Adjust scope and estimates transparently as requirements change.
- Do not manufacture commits or rewrite history to make development appear older.
- Do not use real patient data, confidential customer exports, or regulated information in public examples.
- Confirm eligibility with BYOP organizers before using this repository in a program that excludes ML evaluation or healthcare-data processing.

## License

See [LICENSE](LICENSE) for the repository license.
