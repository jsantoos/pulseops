# M8.4 — Decision × Evolution × Outcome

This increment closes M8 by linking the OIE temporal history to managerial decisions and measured outcomes without claiming causality.

## What changed

- `GET /v1/opportunities/{id}/history` now exposes `decision_impact`.
- `GET /v1/opportunities/temporal` exposes the same decision/outcome context for each operational series.
- Capacity uses `utilization` as its primary operational metric.
- Cancellation/no-show uses `loss_rate` as its primary operational metric.
- The backend separates snapshots created before and after the managerial decision.
- Measured gain is compared with the opportunity potential that existed at the time the outcome was recorded, rather than a later/current estimate.
- The Opportunity detail and consolidated Evolution pages show decision markers, post-decision snapshot counts, measured gain and realization when available.

## Interpretation states

- `not_decided`: no managerial decision exists yet.
- `dismissed`: recommendation was rejected; later changes remain historical context only.
- `awaiting_post_decision_data`: recommendation was accepted/measured but no newer operational snapshot exists yet.
- `post_decision_observed`: at least one new operational snapshot exists after the decision.

## Recommended functional validation

1. Open an operational opportunity and accept it.
2. Open **Evolução**. It should show `0 snapshot(s) após decisão` and `aguardando novo período` if all current snapshots pre-date the decision.
3. Import/analyze a new period containing the same stable OIE opportunity.
4. Reopen **Evolução**. The corresponding series should now show an `Após decisão` row and a comparison between the last pre-decision primary metric and the latest post-decision value.
5. Record a measured outcome in the opportunity detail.
6. Confirm that Evolution and the history panel show measured gain, potential at measurement and observed realization.

The UI deliberately states that these comparisons are temporal/observational and are not proof that the recommendation caused the subsequent change.
