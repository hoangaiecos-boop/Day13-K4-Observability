"""Dashboard 6 panel đọc trực tiếp từ data/logs.jsonl theo config/dashboard.yaml.

Chạy: streamlit run scripts/dashboard.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CONTRACT = yaml.safe_load((REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8"))["dashboard"]
PANELS = {panel["id"]: panel for panel in CONTRACT["panels"]}
LOG_PATH = REPO_ROOT / "data" / "logs.jsonl"


def load_logs() -> pd.DataFrame:
    if not LOG_PATH.exists():
        return pd.DataFrame()
    records = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    df = pd.DataFrame(records)
    if df.empty:
        return df
    df["ts"] = pd.to_datetime(df["ts"], format="ISO8601", utc=True)
    df["minute"] = df["ts"].dt.floor("1min")
    return df


def threshold_label(panel: dict) -> str:
    th = panel["threshold"]
    op = {"lte": "≤", "gte": "≥"}[th["operator"]]
    return f"SLO: {th['aggregation']} {op} {th['value']} {panel['unit']}"


def line_with_threshold(data: pd.DataFrame, x: str, y: str, unit: str, threshold: float | None) -> alt.Chart:
    chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(x=alt.X(f"{x}:T", title="time"), y=alt.Y(f"{y}:Q", title=unit))
    )
    if threshold is None:
        return chart
    rule = (
        alt.Chart(pd.DataFrame({"y": [threshold]}))
        .mark_rule(color="red", strokeDash=[6, 4])
        .encode(y="y:Q")
    )
    return chart + rule


st.set_page_config(page_title=CONTRACT["title"], layout="wide")
st.title(CONTRACT["title"])

df = load_logs()
if df.empty:
    st.warning("Chưa có data/logs.jsonl. Chạy API rồi `python scripts/load_test.py` trước.")
    st.stop()

window = st.sidebar.number_input(
    "Time range (phút)", min_value=5, max_value=1440, value=CONTRACT["time_range_minutes"], step=5
)
st.sidebar.caption(f"Refresh contract: {CONTRACT['refresh_seconds']}s — bấm R hoặc nút Rerun của Streamlit.")

cutoff = df["ts"].max() - pd.Timedelta(minutes=window)
df = df[df["ts"] >= cutoff]

sent = df[df["event"] == "response_sent"]
received = df[df["event"] == "request_received"]
failed = df[df["event"] == "request_failed"] if "event" in df else pd.DataFrame()

st.caption(
    f"Time range: {window} phút (tới {df['ts'].max():%Y-%m-%d %H:%M:%S} UTC) — "
    f"{len(received)} request, {len(sent)} response — nguồn: data/logs.jsonl"
)

# --- Panel 1: Latency percentiles (ms) ---
panel = PANELS["latency"]
st.subheader(f"1. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
if sent.empty:
    st.info("Chưa có response_sent.")
else:
    p50, p95, p99 = sent["latency_ms"].quantile([0.5, 0.95, 0.99])
    c1, c2, c3 = st.columns(3)
    c1.metric("P50", f"{p50:.0f} ms")
    c2.metric("P95", f"{p95:.0f} ms", delta=f"{p95 - panel['threshold']['value']:+.0f} vs SLO",
              delta_color="inverse")
    c3.metric("P99", f"{p99:.0f} ms")
    per_min = sent.groupby("minute")["latency_ms"].quantile(0.95).reset_index(name="p95_ms")
    st.altair_chart(
        line_with_threshold(per_min, "minute", "p95_ms", "ms", panel["threshold"]["value"]),
        use_container_width=True,
    )

# --- Panel 2: Request traffic (requests_per_minute) ---
panel = PANELS["traffic"]
st.subheader(f"2. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
traffic = received.groupby("minute").size().reset_index(name="requests_per_minute")
st.metric("Tổng request", len(received))
st.altair_chart(
    line_with_threshold(traffic, "minute", "requests_per_minute", "req/min", panel["threshold"]["value"]),
    use_container_width=True,
)

# --- Panel 3: Error rate and breakdown (percent) ---
panel = PANELS["errors"]
st.subheader(f"3. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
error_rate = (len(failed) / len(received) * 100) if len(received) else 0.0
st.metric("Error rate", f"{error_rate:.2f} %",
          delta=f"{error_rate - panel['threshold']['value']:+.2f} vs SLO", delta_color="inverse")
if failed.empty:
    st.success("Không có request_failed trong cửa sổ này.")
else:
    st.bar_chart(failed["error_type"].value_counts())

# --- Panel 4: Cost over time (usd) ---
panel = PANELS["cost"]
st.subheader(f"4. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
if not sent.empty:
    st.metric("Tổng cost", f"${sent['cost_usd'].sum():.6f}",
              delta=f"{sent['cost_usd'].sum() - panel['threshold']['value']:+.4f} vs SLO",
              delta_color="inverse")
    cost = sent.groupby("minute")["cost_usd"].sum().reset_index()
    st.altair_chart(
        line_with_threshold(cost, "minute", "cost_usd", "usd/min", None), use_container_width=True
    )

# --- Panel 5: Input and output tokens (tokens) ---
panel = PANELS["tokens"]
st.subheader(f"5. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
if not sent.empty:
    c1, c2 = st.columns(2)
    c1.metric("sum(tokens_in)", int(sent["tokens_in"].sum()))
    c2.metric("sum(tokens_out)", int(sent["tokens_out"].sum()))
    tokens = sent.groupby("minute")[["tokens_in", "tokens_out"]].sum().reset_index()
    st.altair_chart(
        alt.Chart(tokens.melt("minute", var_name="field", value_name="tokens"))
        .mark_line(point=True)
        .encode(x=alt.X("minute:T", title="time"), y=alt.Y("tokens:Q", title="tokens"), color="field:N"),
        use_container_width=True,
    )

# --- Panel 6: Quality proxy (score_0_to_1) ---
panel = PANELS["quality"]
st.subheader(f"6. {panel['title']} ({panel['unit']})")
st.caption(threshold_label(panel))
if not sent.empty:
    mean_q = sent["quality_score"].mean()
    st.metric("mean(quality_score)", f"{mean_q:.3f}",
              delta=f"{mean_q - panel['threshold']['value']:+.3f} vs SLO")
    quality = sent.groupby("minute")["quality_score"].mean().reset_index()
    st.altair_chart(
        line_with_threshold(quality, "minute", "quality_score", "score 0-1", panel["threshold"]["value"]),
        use_container_width=True,
    )
