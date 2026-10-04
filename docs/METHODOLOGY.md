# Experiment methodology

## Decision framework

The primary estimand is the intent-to-treat difference in revenue per randomized user. The decision rule requires:

1. The CUPED-adjusted 95% confidence interval excludes zero.
2. The point estimate meets a predeclared minimum business effect.
3. Refund and latency guardrails remain within tolerance.
4. The sample-ratio mismatch check does not indicate allocation failure.

## CUPED

The pre-experiment spend covariate is centered and multiplied by its estimated relationship with the outcome. This preserves the treatment contrast under randomization while reducing residual variance.

## Validity checks

- Sample-ratio mismatch against the planned 50/50 allocation.
- Standardized pre-spend difference between groups.
- Raw and adjusted effect comparison.
- Guardrail confidence intervals.
- Segment effects labeled as exploratory.
- Sensitivity to the minimum business effect.

## Production policy

Pre-register assignment unit, sample-size target, primary metric, guardrails, decision threshold, analysis window, exclusion rules, novelty period, and sequential-testing policy before launch.
