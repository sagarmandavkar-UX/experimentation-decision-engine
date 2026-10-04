"""Interactive experiment decision dashboard."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from experiment import analyze, make_demo_experiment, threshold_sensitivity, validate_experiment


st.set_page_config(page_title="Experiment Decision Engine", page_icon="⚗️", layout="wide", initial_sidebar_state="collapsed")
st.title("Experiment Decision Engine")
st.caption("Power, CUPED, heterogeneous effects, guardrails, and a predeclared launch rule · seeded demonstration data")

uploaded = st.sidebar.file_uploader("Upload experiment CSV", type="csv")
minimum_effect = st.sidebar.slider("Minimum business effect ($)", 0.0, 3.0, 1.0, 0.25)
data = pd.read_csv(uploaded) if uploaded else make_demo_experiment()
quality = validate_experiment(data)
result = analyze(data, minimum_business_effect=minimum_effect)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Decision", result["decision"])
c2.metric(f"CUPED lift · 95% CI {result['cuped']['ci_low']:.2f}–{result['cuped']['ci_high']:.2f}", f"${result['cuped']['effect']:.2f}")
c3.metric("Variance reduction", f"{result['cuped_variance_reduction']:.0%}")
c4.metric("Sample", f"{quality['rows']:,}", help=f"{quality['treatment']:,} treatment and {quality['control']:,} control")

left, right = st.columns(2)
with left:
    st.subheader("Raw vs. CUPED estimates")
    estimates = pd.DataFrame([{"method": name.upper(), **result[name]} for name in ["raw", "cuped"]])
    chart = go.Figure()
    chart.add_trace(go.Scatter(x=estimates["effect"], y=estimates["method"], mode="markers", marker_size=14, error_x=dict(type="data", symmetric=False, array=estimates["ci_high"] - estimates["effect"], arrayminus=estimates["effect"] - estimates["ci_low"])))
    chart.add_vline(x=0, line_dash="dash")
    chart.add_vline(x=minimum_effect, line_dash="dot", line_color="#DC2626", annotation_text="Business threshold")
    chart.update_layout(xaxis_title="Revenue effect per user ($)", yaxis_title=None)
    st.plotly_chart(chart, width="stretch")
with right:
    st.subheader("Heterogeneous effects")
    segments = pd.DataFrame([{"segment": key, **value} for key, value in result["segment_effects"].items()])
    chart = px.bar(segments, x="segment", y="effect", error_y=segments["ci_high"] - segments["effect"], error_y_minus=segments["effect"] - segments["ci_low"], color="segment", labels={"effect": "Revenue effect ($)"})
    chart.add_hline(y=0, line_color="#334155")
    st.plotly_chart(chart, width="stretch")

st.subheader("Guardrails")
guardrails = pd.DataFrame([{"metric": key, **value} for key, value in result["guardrails"].items()])
st.dataframe(guardrails[["metric", "effect", "ci_low", "ci_high", "p_value"]], hide_index=True, width="stretch")

st.subheader("Decision sensitivity")
sensitivity = threshold_sensitivity(data)
st.plotly_chart(px.line(sensitivity, x="minimum_business_effect", y="effect", markers=True, labels={"minimum_business_effect": "Minimum business effect ($)", "effect": "CUPED effect ($)"}), width="stretch")

with st.expander("Experiment validity checks", expanded=True):
    st.write(result["diagnostics"])
    st.info("Segment effects are diagnostic. Do not ship to a subgroup unless that targeting rule and multiple-testing policy were defined before looking at results.")

st.download_button("Download experiment data", data.to_csv(index=False), "experiment.csv", "text/csv")
