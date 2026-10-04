# Data dictionary

| Field | Definition |
|---|---|
| `treatment` | Random assignment indicator, 0 control / 1 treatment |
| `segment` | Pre-treatment user segment |
| `pre_spend` | Pre-experiment revenue covariate used for CUPED |
| `revenue` | Primary outcome measured during the experiment |
| `refund` | Binary refund guardrail |
| `latency_ms` | Experience-performance guardrail |

Every row represents one randomized user. Outcome rows should be retained even when the user has zero activity; dropping inactive assigned users breaks intent-to-treat analysis.
