"""WaterTriage Streamlit dashboard — college demo console (per corrected plan).

Data layer: FastAPI live endpoints first, baked dashboard/data.json fallback
(same snapshot the Three.js Pages console uses). No hard dependency on backend.
"""

import json
from pathlib import Path

import folium
import pandas as pd
import requests
import streamlit as st
from streamlit_folium import st_folium

st.set_page_config(
    page_title="WaterTriage — Water Quality Risk Dashboard",
    page_icon="💧",
    layout="wide",
)

API_URL = "http://localhost:8000/api"
ROOT = Path(__file__).resolve().parents[1]
BAKED = ROOT / "data.json"
CENTROIDS = ROOT / "assets" / "district_centroids.json"

SEV_COLOR = {"Critical": "#ef4444", "High": "#f97316", "Medium": "#eab308", "Low": "#22c55e"}

st.markdown(
    """<style>
    :root { color-scheme: dark; }
    .stApp { background: #0f172a; color: #f1f5f9; }
    [data-testid="stMetric"] { background: rgba(30,41,59,.72); border: 1px solid rgba(255,255,255,.08);
        border-radius: 12px; padding: 12px 16px; backdrop-filter: blur(16px); }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; }
    [data-testid="stMetricValue"] { font-family: 'JetBrains Mono', ui-monospace, monospace;
        font-variant-numeric: tabular-nums; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; }
    .stTabs [aria-selected="true"] { color: #f1f5f9 !important; }
    </style>""",
    unsafe_allow_html=True,
)


def _get(path, params=None):
    try:
        r = requests.get(f"{API_URL}{path}", params=params or {}, timeout=5)
        if r.status_code == 200:
            return r.json()
    except requests.RequestException:
        pass
    return None


@st.cache_data(ttl=120)
def load_centroids():
    try:
        return json.loads(CENTROIDS.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


@st.cache_data(ttl=60)
def load_bundle():
    live = _get("/dashboard-data")
    if live:
        return live, True
    try:
        return json.loads(BAKED.read_text()), False
    except (OSError, json.JSONDecodeError):
        return {}, False


@st.cache_data(ttl=60)
def load_priority(bundle):
    live = _get("/priority")
    if live:
        return pd.DataFrame(live), True
    rows = bundle.get("priority", [])
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.rename(columns={"worst": "worst_parameter"})
        df["rank"] = range(1, len(df) + 1)
    return df, False


@st.cache_data(ttl=60)
def load_districts(bundle):
    live = _get("/districts")
    if live:
        return pd.DataFrame(live), True
    rows = bundle.get("priority", [])
    if not rows:
        return pd.DataFrame(), False
    df = pd.DataFrame(rows)
    agg = (
        df.groupby(["state", "district"])
        .agg(samples=("score", "size"), avg_score=("score", "mean"))
        .reset_index()
    )
    return agg, False


bundle, live_mode = load_bundle()
df_priority, _ = load_priority(bundle)
df_districts, _ = load_districts(bundle)

st.title("💧 WaterTriage")
st.markdown("### Water quality risk scoring and intervention prioritization — Uttar Pradesh & Bihar")
st.caption(
    "🟢 LIVE — FastAPI backend connected" if live_mode
    else "⚪ OFFLINE — showing baked snapshot from `dashboard/data.json`"
)

kpi = bundle.get("kpi", {})
sb = bundle.get("state_bands", {})

tab_overview, tab_map, tab_priority = st.tabs(
    ["Overview", "District map", "Priority queue"]
)

with tab_overview:
    st.subheader("Key performance indicators")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lab samples scored", f"{kpi.get('samples', len(df_priority)):,}")
    c2.metric("Critical — immediate action", f"{kpi.get('critical', 0):,}")
    c3.metric("High priority", f"{kpi.get('high', 0):,}")
    c4.metric("Registry villages tracked", f"{bundle.get('registry', {}).get('villages', 0):,}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Severity distribution by state")
        if sb:
            st.dataframe(
                pd.DataFrame(sb).T.fillna(0).astype(int),
                use_container_width=True,
            )
        else:
            st.info("No band data available.")
    with right:
        st.markdown("#### State comparison (avg risk score)")
        cmp_rows = bundle.get("compare", [])
        if cmp_rows:
            st.dataframe(
                pd.DataFrame(cmp_rows).sort_values("avg", ascending=False),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No comparison data available.")

    st.markdown("#### District ranking by average risk score")
    if not df_districts.empty and "avg_score" in df_districts.columns:
        disp = df_districts.sort_values("avg_score", ascending=False).reset_index(drop=True)
        st.dataframe(
            disp,
            column_config={
                "avg_score": st.column_config.ProgressColumn(
                    "Average risk score", format="%.2f", min_value=0, max_value=100
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No district data available.")

with tab_map:
    st.subheader("District contamination map")
    st.markdown("Markers are colored by dominant severity band: "
                "**Critical** red · **High** orange · **Medium** yellow · **Low** green.")
    if df_districts.empty:
        st.info("No district data available.")
    else:
        centroids = load_centroids()
        band_filter = st.multiselect(
            "Filter by dominant band", ["Critical", "High", "Medium", "Low"],
            default=["Critical", "High", "Medium", "Low"],
        )
        m = folium.Map(location=[26.2, 82.0], zoom_start=6, tiles="CartoDB dark_matter")
        shown = 0
        for _, row in df_districts.iterrows():
            bc = row.get("band_counts") if isinstance(row.get("band_counts"), dict) else None
            if bc:
                dom = max(bc, key=lambda b: bc.get(b, 0))
            else:
                s = row.get("avg_score") or 0
                dom = "Critical" if s >= 75 else "High" if s >= 50 else "Medium" if s >= 25 else "Low"
            if dom not in band_filter:
                continue
            key = f"{row.get('state', '')}|{row.get('district', '')}"
            if key not in centroids:
                continue
            lat, lon = centroids[key]
            folium.CircleMarker(
                location=[lat, lon],
                radius=9 if dom in ("Critical", "High") else 6,
                color=SEV_COLOR[dom],
                fill=True,
                fill_color=SEV_COLOR[dom],
                fill_opacity=0.75,
                popup=(f"<b>{row.get('district')}</b>, {row.get('state')}<br>"
                       f"samples: {row.get('samples', row.get('sample_count', '—'))}<br>"
                       f"avg score: {row.get('avg_score', '—')} ({dom})"),
            ).add_to(m)
            shown += 1
        st_folium(m, width=1100, height=560)
        st.caption(f"Showing {shown} districts with known coordinates.")

with tab_priority:
    st.subheader("Intervention priority queue")
    st.markdown("Ranked by severity band, then composite score — highest risk first.")
    if df_priority.empty:
        st.info("No priority recommendations available.")
    else:
        f1, f2 = st.columns(2)
        with f1:
            band_sel = st.selectbox("Band", ["All", "Critical", "High", "Medium", "Low"])
        with f2:
            q = st.text_input("Search village / district / contaminant")
        view = df_priority
        if band_sel != "All" and "band" in view.columns:
            view = view[view["band"] == band_sel]
        if q:
            ql = q.lower()
            cols = [c for c in ("village", "district", "worst_parameter") if c in view.columns]
            mask = False
            for c in cols:
                mask = mask | view[c].astype(str).str.lower().str.contains(ql)
            view = view[mask]
        show_cols = [c for c in (
            "rank", "village", "district", "state", "band",
            "score", "worst_parameter", "collected_on",
        ) if c in view.columns]
        st.dataframe(
            view[show_cols].head(200).reset_index(drop=True),
            column_config={
                "score": st.column_config.ProgressColumn(
                    "Score", format="%.2f", min_value=0, max_value=100
                ),
            },
            hide_index=True,
            use_container_width=True,
        )
        st.caption(f"Showing {min(len(view), 200)} of {len(view)} ranked sources.")
