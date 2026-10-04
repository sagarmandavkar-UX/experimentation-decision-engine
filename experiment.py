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
    return pd.DataFrame({"treatment": treatment, "segment": segment, "pre_spend": pre_spend, "revenue": revenue})


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
    decision = "LAUNCH" if cuped["ci_low"] > 0 and cuped["effect"] >= minimum_business_effect else "DO NOT LAUNCH"
    return {
        "raw": raw, "cuped": cuped, "cuped_variance_reduction": float(variance_reduction),
        "segment_effects": segments, "decision": decision,
        "required_n_for_$1_mde": required_sample_size(float(adjusted.std()), 1.0),
    }


def main() -> None:
    out = Path(__file__).parent / "outputs"
    out.mkdir(exist_ok=True)
    result = analyze(make_demo_experiment())
    (out / "decision.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
