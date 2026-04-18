"""Streamlit YouTube Viral Advisor — professional SaaS-style UI.

Design system:
  - Inter font (Google Fonts) with fallbacks.
  - Slate neutral palette, monochrome-first with one accent blue.
  - 4-pt spacing grid, consistent radius (10px), soft shadows.
  - Global Altair chart theme for visual consistency.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import altair as alt
import joblib
import numpy as np
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "processed.csv"
MODEL_PATH = ROOT / "models" / "viral_model.joblib"
METRICS_PATH = ROOT / "models" / "model_metrics.json"
KEYWORDS_PATH = ROOT / "models" / "viral_keywords.json"

DOW_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_WORD_RE = re.compile(r"[A-Za-z]+")
_NUM_RE = re.compile(r"\d")

# ── Design tokens ─────────────────────────────────────────────────────────────
SLATE_900 = "#0f172a"
SLATE_700 = "#334155"
SLATE_600 = "#475569"
SLATE_500 = "#64748b"
SLATE_400 = "#94a3b8"
SLATE_300 = "#cbd5e1"
SLATE_200 = "#e2e8f0"
SLATE_100 = "#f1f5f9"
SLATE_50 = "#f8fafc"

ACCENT = "#2563eb"       # blue-600
ACCENT_SOFT = "#dbeafe"  # blue-100
SUCCESS = "#059669"      # emerald-600
SUCCESS_SOFT = "#d1fae5"
DANGER = "#dc2626"       # red-600
DANGER_SOFT = "#fee2e2"
WARNING = "#d97706"      # amber-600


CUSTOM_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, .stApp,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p,
.stApp label,
.stApp div[data-testid="stMarkdownContainer"],
.stApp [data-testid="stText"],
.stApp .stTextInput input,
.stApp .stSelectbox div,
.stApp .stNumberInput input {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-feature-settings: "cv11", "ss01", "tnum";
}}

#MainMenu, footer, [data-testid="stDeployButton"], [data-testid="stDecoration"] {{
    display: none !important;
}}

.block-container {{
    padding-top: 2.5rem;
    padding-bottom: 4rem;
    max-width: 1320px;
}}

/* Sidebar */
[data-testid="stSidebar"] {{
    background: {SLATE_50};
    border-right: 1px solid {SLATE_200};
}}
[data-testid="stSidebar"] .block-container {{
    padding-top: 2rem;
}}
.sidebar-brand {{
    font-weight: 800;
    font-size: 1.15rem;
    letter-spacing: -0.02em;
    color: {SLATE_900};
    margin-bottom: 2px;
}}
.sidebar-sub {{
    font-size: 0.78rem;
    color: {SLATE_500};
    letter-spacing: 0.02em;
    text-transform: uppercase;
    margin-bottom: 28px;
}}
.sidebar-section-label {{
    font-size: 0.72rem;
    font-weight: 600;
    color: {SLATE_500};
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin: 22px 0 8px 4px;
}}
.sidebar-meta {{
    margin-top: 26px;
    padding-top: 16px;
    border-top: 1px solid {SLATE_200};
    font-size: 0.78rem;
    color: {SLATE_600};
    line-height: 1.6;
}}

/* Hero */
.hero {{
    padding-bottom: 20px;
    border-bottom: 1px solid {SLATE_200};
    margin-bottom: 28px;
}}
.hero .eyebrow {{
    font-size: 0.72rem;
    font-weight: 600;
    color: {ACCENT};
    letter-spacing: 0.12em;
    text-transform: uppercase;
    margin-bottom: 8px;
}}
.hero h1 {{
    font-size: 2.1rem;
    font-weight: 700;
    color: {SLATE_900};
    letter-spacing: -0.025em;
    margin: 0 0 6px 0;
    line-height: 1.15;
}}
.hero p {{
    font-size: 0.98rem;
    color: {SLATE_600};
    margin: 0;
    max-width: 720px;
    line-height: 1.5;
}}

/* Section header */
.section-label {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 0.76rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: {SLATE_500};
    margin: 30px 0 12px 0;
}}
.section-label::before {{
    content: "";
    display: inline-block;
    width: 16px;
    height: 1px;
    background: {SLATE_400};
}}
h3.section-title {{
    font-size: 1.15rem;
    font-weight: 600;
    color: {SLATE_900};
    letter-spacing: -0.01em;
    margin: 8px 0 18px 0;
}}

/* KPI card */
.kpi-grid {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 12px;
}}
.kpi {{
    padding: 16px 18px;
    border: 1px solid {SLATE_200};
    border-radius: 10px;
    background: #ffffff;
    transition: border-color .15s ease;
}}
.kpi:hover {{ border-color: {SLATE_300}; }}
.kpi .label {{
    font-size: 0.7rem;
    color: {SLATE_500};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600;
    margin-bottom: 10px;
}}
.kpi .value {{
    font-size: 1.75rem;
    font-weight: 700;
    color: {SLATE_900};
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
    line-height: 1;
}}
.kpi .sub {{
    font-size: 0.78rem;
    color: {SLATE_500};
    margin-top: 6px;
    font-variant-numeric: tabular-nums;
}}

/* Score module */
.score-wrap {{
    display: grid;
    grid-template-columns: 1.2fr 1fr;
    gap: 20px;
    margin-bottom: 16px;
}}
.score-main {{
    padding: 28px 28px 24px 28px;
    border: 1px solid {SLATE_200};
    border-radius: 12px;
    background: linear-gradient(180deg, #ffffff 0%, {SLATE_50} 100%);
}}
.score-main .eyebrow {{
    font-size: 0.72rem;
    color: {SLATE_500};
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
    margin-bottom: 10px;
}}
.score-main .big {{
    font-size: 3.6rem;
    font-weight: 800;
    color: {SLATE_900};
    letter-spacing: -0.04em;
    line-height: 1;
    font-variant-numeric: tabular-nums;
}}
.score-main .unit {{
    font-size: 1.6rem;
    font-weight: 600;
    color: {SLATE_400};
    margin-left: 4px;
}}
.score-main .desc {{
    color: {SLATE_600};
    font-size: 0.9rem;
    margin-top: 8px;
}}
.score-bar-outer {{
    margin-top: 18px;
    height: 10px;
    background: {SLATE_100};
    border-radius: 999px;
    overflow: hidden;
}}
.score-bar-inner {{
    height: 100%;
    background: linear-gradient(90deg, {ACCENT} 0%, #3b82f6 100%);
    border-radius: 999px;
    transition: width .4s ease;
}}
.score-ticks {{
    display: flex;
    justify-content: space-between;
    margin-top: 6px;
    font-size: 0.72rem;
    color: {SLATE_400};
    font-variant-numeric: tabular-nums;
}}

.score-side {{
    display: flex;
    flex-direction: column;
    gap: 10px;
}}
.score-stat {{
    padding: 14px 16px;
    border: 1px solid {SLATE_200};
    border-radius: 10px;
    background: #ffffff;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
}}
.score-stat .label {{
    font-size: 0.85rem;
    color: {SLATE_600};
}}
.score-stat .value {{
    font-size: 0.95rem;
    font-weight: 600;
    color: {SLATE_900};
    font-variant-numeric: tabular-nums;
}}

/* Benchmark table */
.bench-table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    margin-bottom: 8px;
    font-variant-numeric: tabular-nums;
}}
.bench-table th {{
    text-align: left;
    padding: 10px 14px;
    font-size: 0.74rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: {SLATE_500};
    background: {SLATE_50};
    border-top: 1px solid {SLATE_200};
    border-bottom: 1px solid {SLATE_200};
}}
.bench-table th:first-child {{ border-top-left-radius: 10px; border-left: 1px solid {SLATE_200}; }}
.bench-table th:last-child {{ border-top-right-radius: 10px; border-right: 1px solid {SLATE_200}; }}
.bench-table td {{
    padding: 14px;
    font-size: 0.92rem;
    color: {SLATE_700};
    border-bottom: 1px solid {SLATE_100};
    border-left: 1px solid transparent;
    border-right: 1px solid transparent;
}}
.bench-table td:first-child {{ border-left: 1px solid {SLATE_200}; font-weight: 500; color: {SLATE_900}; }}
.bench-table td:last-child {{ border-right: 1px solid {SLATE_200}; }}
.bench-table tr:last-child td:first-child {{ border-bottom-left-radius: 10px; }}
.bench-table tr:last-child td:last-child {{ border-bottom-right-radius: 10px; }}

/* Status indicator */
.status {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 0.82rem;
    font-weight: 500;
}}
.status .dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    display: inline-block;
}}
.status.ok {{ color: {SUCCESS}; }}
.status.ok .dot {{ background: {SUCCESS}; }}
.status.bad {{ color: {DANGER}; }}
.status.bad .dot {{ background: {DANGER}; }}
.status.warn {{ color: {WARNING}; }}
.status.warn .dot {{ background: {WARNING}; }}

/* Tag chips */
.chip-row {{ line-height: 2.2; }}
.chip {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 3px 4px 3px 0;
    padding: 4px 10px 4px 10px;
    border-radius: 8px;
    background: {SLATE_50};
    border: 1px solid {SLATE_200};
    font-size: 0.82rem;
    color: {SLATE_800 if False else SLATE_700};
    font-weight: 500;
    transition: background .12s ease, border-color .12s ease;
}}
.chip:hover {{ background: #ffffff; border-color: {SLATE_300}; }}
.chip .meta {{
    font-size: 0.72rem;
    color: {SLATE_500};
    font-variant-numeric: tabular-nums;
}}
.chip.hit {{ background: {ACCENT_SOFT}; border-color: #bfdbfe; color: #1e40af; }}
.chip.hit .meta {{ color: #3b82f6; }}

/* Suggestion list */
.suggestion-list {{
    list-style: none;
    padding: 0;
    margin: 0;
}}
.suggestion-list li {{
    padding: 12px 16px;
    border: 1px solid {SLATE_200};
    border-radius: 8px;
    background: #ffffff;
    margin-bottom: 8px;
    font-size: 0.92rem;
    color: {SLATE_700};
    display: flex;
    align-items: flex-start;
    gap: 10px;
    line-height: 1.55;
}}
.suggestion-list li::before {{
    content: "→";
    color: {ACCENT};
    font-weight: 700;
    flex-shrink: 0;
}}

/* Form tweaks */
[data-testid="stForm"] {{
    border: 1px solid {SLATE_200} !important;
    border-radius: 12px !important;
    padding: 22px !important;
    background: #ffffff !important;
}}
.stButton > button, [data-testid="stFormSubmitButton"] button {{
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: -0.005em !important;
    transition: all .12s ease !important;
}}
[data-testid="stFormSubmitButton"] button {{
    background: {DANGER} !important;
    color: #ffffff !important;
    border: 1px solid {DANGER} !important;
    padding: 10px 20px !important;
    box-shadow: 0 1px 2px rgba(220, 38, 38, 0.15) !important;
}}
[data-testid="stFormSubmitButton"] button:hover {{
    background: #b91c1c !important;
    border-color: #b91c1c !important;
    box-shadow: 0 2px 6px rgba(220, 38, 38, 0.25) !important;
}}

/* Alerts / info boxes */
[data-testid="stAlert"] {{ border-radius: 8px !important; }}

/* Dividers */
hr {{ border: none; border-top: 1px solid {SLATE_200}; margin: 28px 0; }}

/* Headings */
h1, h2, h3, h4 {{ color: {SLATE_900}; letter-spacing: -0.015em; }}
</style>
"""


# ── Altair global theme ───────────────────────────────────────────────────────
def _altair_theme():
    return {
        "config": {
            "view": {"stroke": "transparent", "continuousWidth": 400, "continuousHeight": 300},
            "background": "#ffffff",
            "font": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
            "title": {
                "fontSize": 13, "fontWeight": 600, "color": SLATE_900,
                "anchor": "start", "offset": 12, "dy": -2,
            },
            "axis": {
                "domainColor": SLATE_300,
                "gridColor": SLATE_100,
                "tickColor": SLATE_300,
                "labelColor": SLATE_600,
                "labelFontSize": 11,
                "titleColor": SLATE_600,
                "titleFontSize": 11,
                "titleFontWeight": 500,
                "titlePadding": 8,
            },
            "legend": {
                "labelColor": SLATE_600, "titleColor": SLATE_700,
                "labelFontSize": 11, "titleFontSize": 11,
            },
            "range": {
                "category": [ACCENT, SLATE_400, SUCCESS, WARNING, DANGER, SLATE_700],
                "heatmap": ["#f1f5f9", ACCENT],
            },
            "bar": {"cornerRadiusEnd": 3},
        }
    }


alt.themes.register("pro", _altair_theme)
alt.themes.enable("pro")


# ── Loaders ───────────────────────────────────────────────────────────────────

@st.cache_data
def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, usecols=[
        "category", "publish_hour", "publish_dow", "number_of_tags",
        "title_length", "title_word_count", "title_caps_ratio",
        "title_has_number", "title_has_question", "title_has_exclamation",
        "views", "likes", "comments", "like_ratio", "comment_ratio", "tags",
        "country",
    ])


@st.cache_resource
def load_model():
    return joblib.load(MODEL_PATH)


@st.cache_data
def load_metrics() -> dict:
    return json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else {}


@st.cache_data
def load_keywords() -> list[dict]:
    return json.loads(KEYWORDS_PATH.read_text()) if KEYWORDS_PATH.exists() else []


@st.cache_data
def dataset_insights(df: pd.DataFrame) -> dict:
    viral_cut = df["views"].quantile(0.75)
    viral = df[df["views"] >= viral_cut]
    return {
        "best_hours": sorted(viral["publish_hour"].value_counts().head(3).index.tolist()),
        "best_dows": sorted(viral["publish_dow"].value_counts().head(2).index.tolist()),
        "tag_lo": int(viral["number_of_tags"].quantile(0.25)),
        "tag_hi": int(viral["number_of_tags"].quantile(0.75)),
        "title_len_lo": int(viral["title_length"].quantile(0.25)),
        "title_len_hi": int(viral["title_length"].quantile(0.75)),
        "avg_like_ratio": float(df["like_ratio"].mean()),
        "avg_comment_ratio": float(df["comment_ratio"].mean()),
    }


def title_features(title: str) -> dict:
    t = (title or "").strip()
    words = _WORD_RE.findall(t)
    caps = sum(1 for w in words if len(w) >= 2 and w.isupper())
    return {
        "title_length": len(t),
        "title_word_count": len(words),
        "title_caps_ratio": (caps / len(words)) if words else 0.0,
        "title_has_number": int(bool(_NUM_RE.search(t))),
        "title_has_question": int("?" in t),
        "title_has_exclamation": int("!" in t),
    }


def _parse_tags_cell(t) -> list[str]:
    if pd.isna(t):
        return []
    s = str(t).strip()
    if not s or s.lower() == "[none]":
        return []
    sep = "|" if "|" in s else ","
    return [p.strip().lower() for p in re.split(re.escape(sep) + r"|;", s) if p.strip()]


@st.cache_data
def top_tags(df: pd.DataFrame, category: str | None = None, n: int = 15) -> pd.DataFrame:
    subset = df if category in (None, "All") else df[df["category"] == category]
    viral_cut = subset["views"].quantile(0.75)
    viral = subset[subset["views"] >= viral_cut]
    counter: Counter[str] = Counter()
    for cell in viral["tags"].dropna().values:
        counter.update(_parse_tags_cell(cell))
    if not counter:
        return pd.DataFrame(columns=["tag", "count"])
    return pd.DataFrame(counter.most_common(n), columns=["tag", "count"])


# ── UI helpers ────────────────────────────────────────────────────────────────

def hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><div class="eyebrow">{eyebrow}</div>'
        f'<h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def section(label: str, title: str) -> None:
    st.markdown(
        f'<div class="section-label">{label}</div>'
        f'<h3 class="section-title">{title}</h3>',
        unsafe_allow_html=True,
    )


def kpi_grid(items: list[tuple[str, str, str]]) -> None:
    cards = "".join(
        f'<div class="kpi"><div class="label">{lbl}</div>'
        f'<div class="value">{val}</div>'
        f'<div class="sub">{sub}</div></div>'
        for lbl, val, sub in items
    )
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def score_module(score: float, confidence: str, peer_pct: float) -> None:
    w = max(0.5, min(100.0, score))
    band = (
        ("ok", "High viral potential") if score >= 60 else
        ("warn", "Moderate potential") if score >= 30 else
        ("bad", "Below average reach")
    )
    st.markdown(
        f"""
        <div class="score-wrap">
          <div class="score-main">
            <div class="eyebrow">Virality score</div>
            <div><span class="big">{score:.1f}</span><span class="unit">%</span></div>
            <div class="desc">Calibrated probability that this video lands in the top 25 % of trending videos.</div>
            <div class="score-bar-outer"><div class="score-bar-inner" style="width:{w:.2f}%;"></div></div>
            <div class="score-ticks"><span>0%</span><span>25%</span><span>50%</span><span>75%</span><span>100%</span></div>
          </div>
          <div class="score-side">
            <div class="score-stat"><div class="label">Assessment</div>
                <div class="value"><span class="status {band[0]}"><span class="dot"></span>{band[1]}</span></div></div>
            <div class="score-stat"><div class="label">Confidence</div><div class="value">{confidence}</div></div>
            <div class="score-stat"><div class="label">Outperforms</div>
                <div class="value">{peer_pct:.0f}% of trending videos</div></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chips(items: list[dict], highlight: bool = False) -> None:
    klass = "chip hit" if highlight else "chip"
    html = '<div class="chip-row">' + "".join(
        f'<span class="{klass}">{it["label"]}'
        + (f'<span class="meta">{it["meta"]}</span>' if it.get("meta") else "")
        + '</span>'
        for it in items
    ) + '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_suggestions(items: list[str]) -> None:
    html = '<ul class="suggestion-list">' + "".join(f'<li>{t}</li>' for t in items) + '</ul>'
    st.markdown(html, unsafe_allow_html=True)


# ── Charts ────────────────────────────────────────────────────────────────────

def chart_hour_vs_views(df: pd.DataFrame, highlight_hour: int | None = None) -> alt.Chart:
    hourly = df.groupby("publish_hour")["views"].mean().reset_index()
    hourly.columns = ["hour", "avg_views"]
    base = alt.Chart(hourly)
    line = base.mark_line(color=ACCENT, strokeWidth=2).encode(
        x=alt.X("hour:Q", title="Publish hour (UTC)", scale=alt.Scale(domain=[0, 23])),
        y=alt.Y("avg_views:Q", title="Avg views", axis=alt.Axis(format="~s")),
        tooltip=["hour", alt.Tooltip("avg_views:Q", format=",")],
    )
    area = base.mark_area(color=ACCENT, opacity=0.08).encode(
        x="hour:Q", y="avg_views:Q",
    )
    pts = base.mark_circle(color=ACCENT, size=55, stroke="#ffffff", strokeWidth=1.5).encode(
        x="hour:Q", y="avg_views:Q",
        tooltip=["hour", alt.Tooltip("avg_views:Q", format=",")],
    )
    layers = [area, line, pts]
    if highlight_hour is not None:
        rule = alt.Chart(pd.DataFrame({"hour": [highlight_hour]})).mark_rule(
            color=DANGER, strokeDash=[5, 4], strokeWidth=2
        ).encode(x="hour:Q")
        layers.append(rule)
    return alt.layer(*layers).properties(height=280, title="Average views by publish hour")


def chart_stack_viral(df: pd.DataFrame, col: str, bucket: int, title: str) -> alt.Chart:
    b = df.copy()
    b["bucket"] = (b[col] // bucket) * bucket
    cut = b["views"].quantile(0.75)
    b["group"] = np.where(b["views"] >= cut, "Viral", "Non-viral")
    agg = b.groupby(["bucket", "group"])["views"].count().reset_index(name="count")
    return (
        alt.Chart(agg).mark_bar(opacity=0.92).encode(
            x=alt.X("bucket:Q", title=None),
            y=alt.Y("count:Q", title="Videos"),
            color=alt.Color("group:N", scale=alt.Scale(
                domain=["Viral", "Non-viral"], range=[ACCENT, SLATE_300]
            ), legend=alt.Legend(title=None, orient="top")),
            tooltip=["bucket", "group", "count"],
        ).properties(height=240, title=title)
    )


def chart_calibration(curve: list[dict]) -> alt.Chart:
    cdf = pd.DataFrame(curve)
    diag = pd.DataFrame({"x": [0, 1], "y": [0, 1]})
    ref = alt.Chart(diag).mark_line(color=SLATE_300, strokeDash=[4, 4]).encode(x="x:Q", y="y:Q")
    line = alt.Chart(cdf).mark_line(color=ACCENT, strokeWidth=2).encode(
        x=alt.X("bin_mean_pred:Q", title="Predicted probability",
                scale=alt.Scale(domain=[0, 1])),
        y=alt.Y("bin_frac_pos:Q", title="Observed viral rate",
                scale=alt.Scale(domain=[0, 1])),
    )
    pts = alt.Chart(cdf).mark_circle(color=ACCENT, size=60, stroke="#ffffff",
                                      strokeWidth=1.5).encode(
        x="bin_mean_pred:Q", y="bin_frac_pos:Q",
        tooltip=[alt.Tooltip("bin_mean_pred:Q", format=".3f"),
                 alt.Tooltip("bin_frac_pos:Q", format=".3f")],
    )
    return (ref + line + pts).properties(
        height=320, title="Calibration — closer to diagonal = better"
    )


def chart_feature_importance(imp: list[dict]) -> alt.Chart:
    df = pd.DataFrame(imp).sort_values("importance", ascending=False)
    return alt.Chart(df).mark_bar(color=ACCENT).encode(
        x=alt.X("importance:Q", title="Drop in ROC AUC when shuffled"),
        y=alt.Y("feature:N", sort="-x", title=None),
        tooltip=["feature", alt.Tooltip("importance:Q", format=".4f")],
    ).properties(height=26 * len(imp) + 40, title="Permutation feature importance")


def chart_bar(df: pd.DataFrame, x: str, y: str, title: str,
              fmt: str = "~s", height: int = 300) -> alt.Chart:
    return alt.Chart(df).mark_bar(color=ACCENT).encode(
        x=alt.X(f"{x}:Q", axis=alt.Axis(format=fmt), title=None),
        y=alt.Y(f"{y}:N", sort="-x", title=None),
        tooltip=[y, alt.Tooltip(f"{x}:Q", format=",")],
    ).properties(height=height, title=title)


# ── Pages ─────────────────────────────────────────────────────────────────────

def build_suggestions(inputs: dict, insights: dict,
                      keywords_in_title: list[str]) -> list[str]:
    tips: list[str] = []
    tl = inputs["title_length"]
    lo, hi = insights["title_len_lo"], insights["title_len_hi"]
    if tl < lo:
        tips.append(f"Your title is short ({tl} chars). Viral videos fall between {lo} and {hi} characters.")
    elif tl > hi:
        tips.append(f"Your title is long ({tl} chars). Trim toward {lo}–{hi} characters to improve click-through.")
    nt = inputs["number_of_tags"]
    if nt < insights["tag_lo"]:
        tips.append(f"Only {nt} tags. Viral videos typically use {insights['tag_lo']}–{insights['tag_hi']}.")
    elif nt > insights["tag_hi"]:
        tips.append(f"{nt} tags is above the viral range. Focus on {insights['tag_lo']}–{insights['tag_hi']} high-relevance tags.")
    if inputs["publish_hour"] not in insights["best_hours"]:
        hrs = ", ".join(f"{h:02d}:00" for h in insights["best_hours"])
        tips.append(f"Publish window matters. Peak hours are {hrs} UTC.")
    if inputs["publish_dow"] not in insights["best_dows"]:
        days = ", ".join(DOW_NAMES[d] for d in insights["best_dows"])
        tips.append(f"Viral videos skew toward {days}. Consider rescheduling.")
    if inputs["title_caps_ratio"] > 0.5:
        tips.append("Title uses excessive ALL-CAPS — reads as spam. Limit to one CAPS word for emphasis.")
    if not keywords_in_title:
        tips.append("Title contains no viral-associated keywords. See suggestions in the keywords panel.")
    tips.append(
        f"Engagement benchmarks — aim for like-ratio ≥ {insights['avg_like_ratio']:.2%} "
        f"and comment-ratio ≥ {insights['avg_comment_ratio']:.2%}."
    )
    return tips


def _status_html(text: str, ok: bool) -> str:
    kind = "ok" if ok else "bad"
    return f'<span class="status {kind}"><span class="dot"></span>{text}</span>'


def page_predictor(df: pd.DataFrame, model, metrics: dict, keywords: list[dict]) -> None:
    hero("Product", "Viral Advisor",
         "Predict a video's chance of reaching the top 25 % of trending videos. "
         "Uses a gradient-boosted, calibrated model with NLP title features.")

    section("01", "Model quality")
    kpi_grid([
        ("Test ROC AUC", f"{metrics.get('test_roc_auc', 0):.3f}", "held-out 20 %"),
        ("CV ROC AUC", f"{metrics.get('cv_roc_auc_mean', 0):.3f}",
         f"± {metrics.get('cv_roc_auc_std', 0):.3f}  ·  5-fold"),
        ("PR AUC", f"{metrics.get('test_pr_auc', 0):.3f}", "average precision"),
        ("Brier", f"{metrics.get('brier_score', 0):.3f}", "calibration error"),
    ])

    insights = dataset_insights(df)
    categories = sorted(df["category"].dropna().unique().tolist())
    countries = sorted(df["country"].dropna().unique().tolist())

    section("02", "Video details")
    with st.form("predict_form"):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Title", value="Top 10 BEST Moments of 2026")
            category = st.selectbox("Category", categories,
                                     index=categories.index("Entertainment")
                                     if "Entertainment" in categories else 0)
            country = st.selectbox("Country", countries,
                                    index=countries.index("US") if "US" in countries else 0)
            num_tags = st.number_input("Number of tags", 0, 80, 15)
        with c2:
            hour = st.slider("Publish hour (UTC)", 0, 23, 15)
            dow = st.selectbox("Publish day", list(range(7)),
                                format_func=lambda i: DOW_NAMES[i], index=4)
        submitted = st.form_submit_button("Analyze video", use_container_width=True)

    if not submitted:
        st.info("Fill in the details above and click **Analyze video**.", icon="ℹ️")
        return

    tf = title_features(title)
    row = {**tf, "number_of_tags": int(num_tags), "publish_hour": int(hour),
           "publish_dow": int(dow), "category": category, "country": country}
    X = pd.DataFrame([row])
    try:
        prob = float(model.predict_proba(X)[0, 1])
    except Exception:
        prob = float(model.predict_proba(X.drop(columns=["country"]))[0, 1])
    score = round(prob * 100, 1)

    # Confidence label: spread between average dataset prior and prediction.
    confidence = ("High" if abs(prob - 0.25) > 0.25 else
                  "Medium" if abs(prob - 0.25) > 0.1 else "Low")
    peer_pct = prob * 100

    section("03", "Virality score")
    score_module(score, confidence, peer_pct)

    # Keyword hits
    kw_lookup = {k["word"]: k for k in keywords}
    title_words = {w.lower() for w in _WORD_RE.findall(title)}
    hits = sorted(
        [kw_lookup[w] for w in title_words if w in kw_lookup],
        key=lambda k: k["lift"], reverse=True,
    )

    section("04", "Benchmark comparison")
    rows = [
        ("Number of tags", num_tags,
         f"{insights['tag_lo']}–{insights['tag_hi']}",
         insights["tag_lo"] <= num_tags <= insights["tag_hi"],
         "in range", "outside range"),
        ("Title length", f"{tf['title_length']} chars",
         f"{insights['title_len_lo']}–{insights['title_len_hi']} chars",
         insights["title_len_lo"] <= tf["title_length"] <= insights["title_len_hi"],
         "in range", "outside range"),
        ("Publish hour", f"{hour:02d}:00 UTC",
         ", ".join(f"{h:02d}:00" for h in insights["best_hours"]),
         hour in insights["best_hours"], "peak hour", "off-peak"),
        ("Publish day", DOW_NAMES[dow],
         ", ".join(DOW_NAMES[d] for d in insights["best_dows"]),
         dow in insights["best_dows"], "peak day", "off-peak"),
        ("Viral keywords in title", f"{len(hits)} hit(s)",
         "≥ 1 recommended", bool(hits), "hit", "no hits"),
    ]
    body = "".join(
        f"<tr><td>{m}</td><td>{v}</td><td>{b}</td>"
        f"<td>{_status_html(sok if ok else sbad, ok)}</td></tr>"
        for m, v, b, ok, sok, sbad in rows
    )
    st.markdown(
        '<table class="bench-table">'
        '<thead><tr><th>Metric</th><th>Your value</th>'
        '<th>Viral benchmark</th><th>Status</th></tr></thead>'
        f'<tbody>{body}</tbody></table>',
        unsafe_allow_html=True,
    )

    section("05", "Recommendations")
    render_suggestions(build_suggestions(row, insights, [h["word"] for h in hits]))

    section("06", "Viral keywords")
    if hits:
        st.markdown("**Detected in your title** (higher lift = more viral-indicative)")
        render_chips(
            [{"label": h["word"], "meta": f"×{h['lift']:.2f}"} for h in hits],
            highlight=True,
        )
    else:
        st.markdown(
            f'<div style="padding:12px 14px;border:1px solid {SLATE_200};'
            f'border-radius:8px;color:{SLATE_600};font-size:0.9rem;background:{SLATE_50};">'
            'No viral-associated keywords detected in your title.</div>',
            unsafe_allow_html=True,
        )
    st.markdown("**Suggestions** (unused high-lift words from trending titles)")
    suggest_pool = [k for k in keywords if k["word"] not in title_words][:15]
    render_chips([{"label": k["word"], "meta": f"×{k['lift']:.2f}"} for k in suggest_pool])

    section("07", "Trending tags")
    scope = st.selectbox("Scope", ["All categories", category],
                         label_visibility="collapsed")
    tags_df = top_tags(df, None if scope == "All categories" else category, n=12)
    if tags_df.empty:
        st.caption("No tag data available.")
    else:
        col1, col2 = st.columns([1, 1.1])
        with col1:
            render_chips([{"label": t, "meta": f"{int(c):,}"}
                          for t, c in zip(tags_df["tag"], tags_df["count"])])
        with col2:
            st.altair_chart(chart_bar(tags_df, "count", "tag",
                                       f"Top tags — {scope}", fmt=",", height=340),
                             use_container_width=True)

    section("08", "Timing insight")
    st.altair_chart(chart_hour_vs_views(df, highlight_hour=hour),
                    use_container_width=True)
    st.caption(f"Red line marks your selected publish hour ({hour:02d}:00 UTC).")


def page_dashboard(df: pd.DataFrame) -> None:
    hero("Analytics", "Dashboard",
         "Aggregate patterns across the trending dataset — category performance, timing, and engagement benchmarks.")

    section("Overview", "Dataset snapshot")
    kpi_grid([
        ("Videos", f"{len(df):,}", "total trending records"),
        ("Categories", f"{df['category'].nunique()}", "after cleaning"),
        ("Median like ratio", f"{df['like_ratio'].median():.2%}", "likes / views"),
        ("Median comment ratio", f"{df['comment_ratio'].median():.3%}", "comments / views"),
    ])

    cat = (df.groupby("category")["views"].median()
           .sort_values(ascending=False).head(10).reset_index())
    cat.columns = ["category", "median_views"]

    section("Category", "Performance breakdown")
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_bar(cat, "median_views", "category",
                                   "Top 10 categories — median views", height=330),
                         use_container_width=True)
    with col2:
        lr = (df.groupby("category")["like_ratio"].median()
              .sort_values(ascending=False).head(10).reset_index())
        lr.columns = ["category", "median_like_ratio"]
        st.altair_chart(
            alt.Chart(lr).mark_bar(color=ACCENT).encode(
                x=alt.X("median_like_ratio:Q", axis=alt.Axis(format=".1%"), title=None),
                y=alt.Y("category:N", sort="-x", title=None),
                tooltip=["category", alt.Tooltip("median_like_ratio:Q", format=".2%")],
            ).properties(height=330, title="Median like ratio by category"),
            use_container_width=True,
        )

    section("Timing", "When do viral videos get published?")
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_hour_vs_views(df), use_container_width=True)
    with col2:
        dow = df.groupby("publish_dow")["views"].mean().reset_index()
        dow["day"] = dow["publish_dow"].map(lambda i: DOW_NAMES[int(i)])
        st.altair_chart(
            alt.Chart(dow).mark_bar(color=ACCENT).encode(
                x=alt.X("day:N", sort=DOW_NAMES, title=None),
                y=alt.Y("views:Q", axis=alt.Axis(format="~s"), title="Avg views"),
                tooltip=["day", alt.Tooltip("views:Q", format=",")],
            ).properties(height=280, title="Average views by day of week"),
            use_container_width=True,
        )

    section("Distributions", "What separates viral from non-viral?")
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_stack_viral(df, "number_of_tags", 5,
                                           "Tag count: viral vs non-viral"),
                         use_container_width=True)
    with col2:
        st.altair_chart(chart_stack_viral(df, "title_length", 10,
                                           "Title length: viral vs non-viral"),
                         use_container_width=True)


def page_model_insights(metrics: dict, keywords: list[dict]) -> None:
    hero("Internals", "Model Insights",
         "How the classifier was trained, how well it calibrates, and which features drive the prediction.")

    if not metrics:
        st.warning("No metrics file found. Retrain the model to populate it.")
        return

    section("Metrics", "Model quality")
    kpi_grid([
        ("Test ROC AUC", f"{metrics['test_roc_auc']:.3f}", "held-out test set"),
        ("CV ROC AUC", f"{metrics['cv_roc_auc_mean']:.3f}",
         f"± {metrics['cv_roc_auc_std']:.3f}  ·  5-fold"),
        ("PR AUC", f"{metrics['test_pr_auc']:.3f}", "average precision"),
        ("Brier", f"{metrics['brier_score']:.3f}", "calibration error"),
    ])

    section("Algorithm", "How it works")
    st.markdown(
        f"""
        <div style="padding:16px 20px; border:1px solid {SLATE_200};
                    border-radius:10px; background: #ffffff; line-height:1.7;
                    color: {SLATE_700}; font-size:0.93rem;">
        <strong style="color:{SLATE_900};">Architecture.</strong>
        HistGradientBoostingClassifier (300 iterations, depth 8, learning rate 0.08,
        L2 = 1.0, early stopping on 10% validation split) wrapped in
        CalibratedClassifierCV (isotonic, 3 inner folds) for reliable probabilities.<br><br>
        <strong style="color:{SLATE_900};">Features.</strong>
        9 numeric (title length, word count, CAPS ratio, has number / question / exclamation,
        number of tags, publish hour, publish day-of-week) plus 2 one-hot categoricals
        (category, country).<br><br>
        <strong style="color:{SLATE_900};">Target.</strong>
        Binary — video reaches views ≥ 75th percentile within the training set (≈ 25 % positive class).
        </div>
        """,
        unsafe_allow_html=True,
    )

    section("Diagnostics", "Feature importance & calibration")
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(chart_feature_importance(metrics["feature_importance"]),
                        use_container_width=True)
    with col2:
        st.altair_chart(chart_calibration(metrics["calibration_curve"]),
                        use_container_width=True)

    section("Classification", "Per-class performance (threshold = 0.5)")
    rep = metrics["test_report"]
    rows = []
    for key in ["0", "1", "macro avg", "weighted avg"]:
        if key in rep:
            r = rep[key]
            rows.append({
                "Class": "Non-viral" if key == "0" else ("Viral" if key == "1" else key.title()),
                "Precision": f"{r['precision']:.3f}",
                "Recall": f"{r['recall']:.3f}",
                "F1": f"{r['f1-score']:.3f}",
                "Support": f"{int(r.get('support', 0)):,}",
            })
    st.dataframe(pd.DataFrame(rows).set_index("Class"),
                 use_container_width=True, hide_index=False)

    section("NLP", "Top viral keywords by lift")
    st.caption(
        "Lift = P(word | viral) / P(word). Values above 1 mean the word appears "
        "disproportionately often in top-25% videos."
    )
    kdf = pd.DataFrame(keywords[:20])
    if not kdf.empty:
        st.altair_chart(
            alt.Chart(kdf).mark_bar(color=ACCENT).encode(
                x=alt.X("lift:Q", title="Lift"),
                y=alt.Y("word:N", sort="-x", title=None),
                tooltip=["word", "count", "viral_count", alt.Tooltip("lift:Q", format=".3f")],
            ).properties(height=26 * len(kdf) + 40),
            use_container_width=True,
        )


# ── App entry ─────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(page_title="YouTube Viral Advisor",
                       layout="wide", initial_sidebar_state="expanded")
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not DATA_PATH.exists():
        st.error(f"Missing {DATA_PATH}. Run: python rq2_project/analysis.py")
        st.stop()
    if not MODEL_PATH.exists():
        st.error(f"Missing {MODEL_PATH}. Run: python rq2_project/model.py")
        st.stop()

    df = load_data()
    model = load_model()
    metrics = load_metrics()
    keywords = load_keywords()

    with st.sidebar:
        st.markdown(
            '<div class="sidebar-brand">YT Viral Advisor</div>'
            '<div class="sidebar-sub">Trending intelligence</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="sidebar-section-label">Product</div>',
                    unsafe_allow_html=True)
        page = st.radio(
            "nav", ["Viral Advisor", "Dashboard", "Model Insights"],
            label_visibility="collapsed",
        )
        total = metrics.get("n_train", 0) + metrics.get("n_test", 0)
        st.markdown(
            f'<div class="sidebar-meta">'
            f'<strong style="color:{SLATE_700};">Model</strong><br>'
            f'Gradient-boosted · calibrated<br>'
            f'Trained on {total:,} videos<br>'
            f'Test ROC AUC: <strong>{metrics.get("test_roc_auc", 0):.3f}</strong>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if page == "Dashboard":
        page_dashboard(df)
    elif page == "Model Insights":
        page_model_insights(metrics, keywords)
    else:
        page_predictor(df, model, metrics, keywords)


if __name__ == "__main__":
    main()
