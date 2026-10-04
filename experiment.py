"""A/B testing with power, CUPED variance reduction, segments, and a decision rule."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm


def make_demo_experiment(seed: int = 21, n: int = 12000) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    pre_spend = rng.gamma(2.0, 22.0, n)
    treatment = rng.integers(0, 2, n)
    segment = rng.choice(["new", "returning"], n, p=[0.45, 0.55])
    treatment_effect = np.where(segment == "returning", 2.8, 0.8)
    revenue = 15 + 0.55 * pre_spend + treatment * treatment_effect + rng.normal(0, 18, n)
    refund = rng.binomial(1, np.clip(0.035 + (segment == "new") * 0.008, 0, 1))
    latency_ms = np.maximum(50, rng.normal(420 + treatment * 8, 65, n))
    return pd.DataFrame({"treatment": treatment, "segment": segment, "pre_spend": pre_spend, "revenue": revenue, "refund": refund, "latency_ms": latency_ms})


def required_sample_size(baseline_sd: float, mde: float, alpha: float = 0.05, power: float = 0.8) -> int:
    z_alpha = norm.ppf(1 - alpha / 2)
    z_power = norm.ppf(power)
    return int(np.ceil(2 * ((z_alpha + z_power) * baseline_sd / mde) ** 2))


def _difference(values: pd.Series, treatment: pd.Series) -> dict[str, float]:
    control = values[treatment == 0]
    treated = values[treatment == 1]
    effect = float(treated.mean() - control.mean())
    se = float(np.sqrt(treated.var(ddof=1) / len(treated) + control.var(ddof=1) / len(control)))
    p = float(2 * norm.sf(abs(effect / se)))
    return {"effect": effect, "se": se, "ci_low": effect - 1.96 * se, "ci_high": effect + 1.96 * se, "p_value": p}


def analyze(data: pd.DataFrame, minimum_business_effect: float = 1.0) -> dict:
    theta = float(data["revenue"].cov(data["pre_spend"]) / data["pre_spend"].var())
    adjusted = data["revenue"] - theta * (data["pre_spend"] - data["pre_spend"].mean())
    raw = _difference(data["revenue"], data["treatment"])
    cuped = _difference(adjusted, data["treatment"])
    segments = {name: _difference(group["revenue"], group["treatment"]) for name, group in data.groupby("segment")}
    variance_reduction = 1 - adjusted.var() / data["revenue"].var()
    diagnostics = experiment_diagnostics(data)
    guardrails = {
        "refund_rate_difference": _difference(data["refund"], data["treatment"]),
        "latency_ms_difference": _difference(data["latency_ms"], data["treatment"]),
    }
    guardrails_pass = guardrails["refund_rate_difference"]["ci_high"] < 0.01 and guardrails["latency_ms_difference"]["ci_high"] < 25
    decision = "LAUNCH" if cuped["ci_low"] > 0 and cuped["effect"] >= minimum_business_effect and guardrails_pass and diagnostics["srm_p_value"] >= 0.01 else "DO NOT LAUNCH"
    return {
        "raw": raw, "cuped": cuped, "cuped_variance_reduction": float(variance_reduction),
        "segment_effects": segments, "guardrails": guardrails, "diagnostics": diagnostics, "decision": decision,
        "required_n_for_$1_mde": required_sample_size(float(adjusted.std()), 1.0),
    }


def validate_experiment(data: pd.DataFrame) -> dict[str, int]:
    required = {"treatment", "segment", "pre_spend", "revenue", "refund", "latency_ms"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    if not set(data["treatment"].dropna().unique()).issubset({0, 1}):
        raise ValueError("treatment must be binary")
    return {"rows": len(data), "control": int((data["treatment"] == 0).sum()), "treatment": int((data["treatment"] == 1).sum())}


def experiment_diagnostics(data: pd.DataFrame) -> dict[str, float]:
    """Return sample-ratio mismatch and pre-treatment balance diagnostics."""
    validate_experiment(data)
    treatment_n = int(data["treatment"].sum())
    n = len(data)
    z = (treatment_n - n * 0.5) / np.sqrt(n * 0.25)
    srm_p = float(2 * norm.sf(abs(z)))
    control = data.loc[data["treatment"] == 0, "pre_spend"]
    treated = data.loc[data["treatment"] == 1, "pre_spend"]
    pooled_sd = np.sqrt((control.var(ddof=1) + treated.var(ddof=1)) / 2)
    standardized_difference = float((treated.mean() - control.mean()) / pooled_sd)
    return {"srm_p_value": srm_p, "pre_spend_standardized_difference": standardized_difference}


def threshold_sensitivity(data: pd.DataFrame, thresholds: tuple[float, ...] = (0.0, 0.5, 1.0, 1.5, 2.0)) -> pd.DataFrame:
    """Show how the launch recommendation changes with the business threshold."""
    rows = []
    for threshold in thresholds:
        result = analyze_once(data, threshold)
        rows.append({"minimum_business_effect": threshold, **result})
    return pd.DataFrame(rows)


def analyze_once(data: pd.DataFrame, minimum_business_effect: float) -> dict[str, float | str]:
    theta = float(data["revenue"].cov(data["pre_spend"]) / data["pre_spend"].var())
    adjusted = data["revenue"] - theta * (data["pre_spend"] - data["pre_spend"].mean())
    estimate = _difference(adjusted, data["treatment"])
    return {"effect": estimate["effect"], "ci_low": estimate["ci_low"], "ci_high": estimate["ci_high"], "meets_threshold": estimate["ci_low"] > 0 and estimate["effect"] >= minimum_business_effect}


def main() -> None:
    out = Path(__file__).parent / "outputs"
    out.mkdir(exist_ok=True)
    data = make_demo_experiment()
    result = analyze(data)
    threshold_sensitivity(data).to_csv(out / "threshold_sensitivity.csv", index=False)
    (out / "decision.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
