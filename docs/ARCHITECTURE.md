# Architecture v0.1

## Product vs engine

- **PulseOps** is the customer-facing healthcare product.
- **OIE** is the framework-independent Operational Intelligence Engine.

## Dependency rule

The core domain must not import web frameworks, ORMs, databases, cloud SDKs, or LLM clients.

## Initial flow

`canonical operational facts -> deterministic analyzers -> structured Opportunity[]`

A generative model may later create a narrative from an Opportunity, but it must not alter the underlying evidence, financial estimate, confidence, or score.

## AI engineering guardrails

1. Prefer deterministic/statistical methods for claims that can be calculated.
2. Keep provenance/evidence with each generated opportunity.
3. Separate prediction confidence from business impact.
4. Version rules, models, prompts, schemas, and evaluation datasets.
5. Evaluate offline before deploying model/prompt changes.
6. Never use patient-identifying information in prompts unless an approved architecture explicitly requires and protects it.
7. Human approval is mandatory before any future system performs operational actions.
