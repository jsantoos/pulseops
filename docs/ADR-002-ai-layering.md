# ADR-002 — Deterministic, predictive and cognitive AI layers

**Status:** Accepted  
**Date:** 2026-08-20

## Decision
OIE separates intelligence into deterministic analytics, probabilistic prediction, and cognitive/LLM presentation. Financial calculations and operational facts must never depend on an LLM response.

## Consequences
Every recommendation can retain machine-readable evidence and calculations. LLMs may summarize or explain an already-structured decision but cannot silently mutate its score, financial impact, or source facts.
