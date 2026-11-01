# ADR-003 — Predictive models require temporal evaluation

**Status:** Accepted  
**Date:** 2026-08-20

## Decision
Time-dependent operational predictions use chronological train/validation splits. Random splits are not the default because they can leak future operational patterns into training.

A candidate model must be compared with a documented baseline and evaluated at least for probability quality (Brier score/log loss), calibration and operational utility before promotion.
