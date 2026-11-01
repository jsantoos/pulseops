# PulseOps / OIE

**Operational Intelligence for Healthcare**

PulseOps is a healthcare operations management platform designed to help diagnostic clinics identify inefficiencies, optimize resource utilization, and support data-driven operational decisions.

The platform transforms operational data into explainable opportunities, helping managers understand capacity gaps, appointment cancellations, idle resources, and potential financial impact.

**OIE (Operational Intelligence Engine)** is the reusable decision-intelligence core powering PulseOps. It is designed to operate independently of the web application, database, or large language models.

## 1. Project Overview

Diagnostic clinics manage equipment availability, appointments, cancellations, and service execution across multiple operational processes.

When this information is fragmented, identifying inefficiencies and prioritizing improvements becomes difficult.

PulseOps addresses this challenge by providing a structured workflow:

1. Ingest operational datasets.
2. Validate and normalize the information.
3. Analyze resource utilization and operational losses.
4. Identify opportunities for improvement.
5. Estimate potential operational and financial impact.
6. Present explainable findings to support management decisions.
7. Support decision-making and follow-up activities.

The objective is to transform operational information into actionable insights while maintaining transparency, traceability, and auditability.

## 2. Core Features

### Operational Data Ingestion

- Structured operational dataset ingestion.
- CSV bundle uploads.
- Equipment, availability, appointment, and execution data.
- Data validation and normalization.
- Organization-based dataset processing.

### Operational Intelligence Engine

- Capacity utilization analysis.
- Idle-resource identification.
- Appointment cancellation and no-show analysis.
- Operational opportunity detection.
- Financial impact estimation.
- Evidence-based opportunity prioritization.
- Explainable calculations and confidence indicators.

### Predictive and Decision Intelligence

- Leakage-safe cancellation features.
- Transparent Bayesian probability baseline.
- Logistic regression challenger.
- Chronological evaluation.
- Brier score, log-loss, and calibration metrics.
- Champion/challenger model governance.
- Threshold-based decision metrics.
- Economic decision policies based on expected net operational value.
- Idle-slot recovery ranking.

Predictive components are experimental and require appropriate validation before production use. Synthetic evaluation does not establish real-world predictive performance.

### Business Dashboard

- Operational opportunity visualization.
- Business-oriented Portuguese terminology.
- Human-readable percentages, durations, and BRL values.
- Priority indicators.
- Detailed opportunity explanations.
- Separation of observed data, calculated results, and assumptions.
- Decision workflows and opportunity status tracking.

Financial estimates represent potential opportunities, not guaranteed revenue.

## 3. Technology Stack

| Layer | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Frontend | Next.js, React, TypeScript |
| Database | PostgreSQL |
| ORM and migrations | SQLAlchemy, Alembic |
| Data processing | Python-based analytics |
| API communication | REST |
| Testing | pytest |
| Code quality | Ruff |
| Package management | uv |
| Development infrastructure | Docker / Docker Compose |

## 4. Architecture

PulseOps follows a modular architecture that separates user interfaces, application services, persistence, and domain intelligence.

```text
                    PulseOps Web
                 Next.js / React
                        |
                        v
                    FastAPI
                        |
             Application Services
                        |
              +---------+---------+
              |                   |
              v                   v
          PostgreSQL         OIE Core
                              |
                     +--------+--------+
                     |                 |
                     v                 v
              Operational         Decision
               Analytics        Intelligence
                     |                 |
                     +--------+--------+
                              |
                              v
                     Explainable Results
```

### PulseOps Web

The user-facing application for exploring operational indicators, reviewing opportunities, and supporting business decisions.

### PulseOps API

The backend application responsible for dataset ingestion, API endpoints, business workflows, and persistence.

### OIE Core

A reusable, framework-independent domain engine responsible for operational calculations, predictive components, opportunity generation, and decision policies.

The OIE Core can be tested independently from the web application and database.

## 5. Repository Organization

Key project directories include:

```text
pulseops/
├── apps/
│   └── web/
├── packages/
│   └── oie_core/
├── datasets/
│   └── csv-sample/
├── migrations/
├── scripts/
├── docs/
├── README.md
└── LICENSE
```

The repository also contains backend application components and supporting configuration files.

## 6. Getting Started

### Prerequisites

Install the tools required by the components you intend to run:

- Python
- uv
- Node.js and npm
- PostgreSQL
- Docker and Docker Compose, where applicable

### Install Python Dependencies

From the repository root:

```bash
uv sync
```

### Run Tests

```bash
uv run pytest
```

### Run Code Quality Checks

```bash
uv run ruff check .
```

### Run Sample Analysis

```bash
uv run python scripts/analyze_sample.py
```

### Run OIE Core Tests

```bash
PYTHONPATH=packages/oie_core/src pytest -q
```

### Run Predictive Evaluation

```bash
PYTHONPATH=packages/oie_core/src python scripts/evaluate_m2.py
```

These commands cover the documented OIE workflows. Backend API startup and database initialization depend on the application's configuration and migration setup.

## 7. CSV Bundle Ingestion

PulseOps supports importing operational exports through the API.

Example:

```bash
curl -X POST \
  "http://127.0.0.1:8000/v1/datasets/csv-bundle?organization_id=$ORG_ID" \
  -F "equipment=@datasets/csv-sample/equipment.csv" \
  -F "availability=@datasets/csv-sample/availability.csv" \
  -F "appointments=@datasets/csv-sample/appointments.csv" \
  -F "executions=@datasets/csv-sample/executions.csv"
```

After uploading a dataset, analyze it using the returned dataset identifier:

```http
POST /v1/datasets/{dataset_id}/analyze
```

The analysis generates operational findings and opportunities based on the available data.

## 8. Running the Frontend

Navigate to the web application:

```bash
cd apps/web
```

Create the local environment configuration:

```bash
cp .env.local.example .env.local
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

Expected local addresses:

| Service | Address |
|---|---|
| Frontend | http://127.0.0.1:3000 |
| Backend API | http://127.0.0.1:8000 |

The backend API must be running and configured correctly for the frontend to access operational data.

## 9. Engineering Principles

PulseOps is designed around the following principles:

**Domain-first architecture:** business rules and calculations should remain independent of infrastructure frameworks.

**Deterministic analytics first:** operational findings should originate from verifiable calculations rather than generated text.

**Explainability:** opportunities must include supporting evidence, assumptions, and confidence indicators where applicable.

**Financial transparency:** potential gains should be calculated explicitly and must not be presented as guaranteed outcomes.

**Separation of concerns:** application workflows, persistence, domain calculations, and user interfaces should have clear responsibilities.

**Testability:** core business logic should be independently testable.

**Responsible AI:** language models, when used, may explain structured findings but must not invent operational evidence.

**Data protection:** public sample datasets should not contain patient-identifying information or confidential customer data.

## 10. Development Milestones

| Milestone | Scope |
|---|---|
| M0 | Framework-independent operational intelligence foundation |
| M2 | Predictive capacity and idle-slot recovery |
| M3 | Decision intelligence and economic policies |
| M5.1 | CSV bundle ingestion |
| M6 | PulseOps Web |
| M6.1A | Business UX and explainability |

Additional milestone documentation and validation artifacts are available in the `docs/` directory.

### M6.1A — Business UX and Explainability

This milestone focuses on making operational findings understandable to nontechnical users.

Improvements include:

- Portuguese business terminology.
- Readable operational and financial values.
- Business-oriented opportunity priorities.
- Transparent calculation explanations.
- Explicit distinction between observations and estimates.
- Prevention of duplicate decisions for closed or measured opportunities.

## 11. Roadmap

The following areas represent potential future development work, subject to project priorities:

- [ ] Expand automated backend and frontend testing.
- [ ] Improve dataset validation and error reporting.
- [ ] Enhance operational dashboard navigation and filtering.
- [ ] Improve API documentation and developer onboarding.
- [ ] Expand observability and structured logging.
- [ ] Improve accessibility and responsive design.
- [ ] Refactor application services to strengthen module boundaries.
- [ ] Improve integration testing and CI workflows.
- [ ] Expand synthetic demonstration datasets.
- [ ] Improve opportunity lifecycle and reporting workflows.

Roadmap items are not commitments to specific delivery dates. Detailed tasks and implementation progress can be tracked through GitHub Issues.

## 12. Data Privacy and Responsible Use

PulseOps is intended to support operational analysis and decision-making.

The public repository should contain only synthetic, anonymized, or otherwise appropriately shareable demonstration data.

Production deployments involving healthcare information require appropriate privacy, security, access-control, and regulatory safeguards.

The platform does not provide medical diagnoses or clinical treatment recommendations.

## 13. Project Status

**Status: Active development**

PulseOps is an evolving software project focused on operational intelligence, explainable analytics, and workflow improvement.

Features and APIs may change as the architecture and product capabilities evolve.

## 14. License

This project is licensed under the MIT License.

See the [LICENSE](LICENSE) file for details.
