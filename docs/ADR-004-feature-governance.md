# ADR-004 — Versioned and leakage-safe features

**Status:** Accepted  
**Date:** 2026-08-20

## Decision
Predictive features are centrally defined, versioned and computed only from information available at prediction time. M2 cancellation features intentionally exclude patient identity and post-outcome fields.

## Rationale
This limits target leakage, improves reproducibility and supports data minimization for LGPD-sensitive deployments.
