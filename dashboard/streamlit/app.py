import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import random

# Page configuration
st.set_page_config(
    page_title="WaterTriage — Water Quality Risk Dashboard",
    page_icon="💧",
    layout="wide"
)

# Constants
API_URL = "http://localhost:8000/api"

# District Coordinates for Jitter Map
DISTRICT_COORDS = {
    # Bihar
    "Katihar": (25.55, 87.57),
    "Araria": (26.15, 87.43),
    # Uttar Pradesh
    "Unnao": (26.54, 80.49),
    "Firozabad": (27.15, 78.40),
    "Hardoi": (27.38, 80.12),
    "Pratapgarh": (25.92, 81.86),
    "Rae Bareli": (26.22, 81.24),
    "Ballia": (25.76, 84.15),
    "Amethi": (26.16, 81.81),
    "Fatehpur": (25.93, 80.81),
    "Ghazipur": (25.58, 83.58),
    "Kannauj": (27.05, 79.91),
    "Shamli": (29.45, 77.31),
    "Sonbhadra": (24.68, 83.06),
    "Prayagraj": (25.45, 81.84),
    "Mathura": (27.49, 77.67)
}

# Fetching helpers
def check_api_status():
    try:
        response = requests.get("http://localhost:8000/")
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        return False

@st.cache_data(ttl=60)
def get_districts():
    try:
        r = requests.get(f"{API_URL}/districts")
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Error fetching districts: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_risk_scores(severity_band=None, parameter=None):
    try:
        params = {}
        if severity_band:
            params["severity_band"] = severity_band
        if parameter:
            params["parameter"] = parameter
        
        r = requests.get(f"{API_URL}/scoring", params=params)
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Error fetching risk scores: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_priority_queue():
    try:
        r = requests.get(f"{API_URL}/priority")
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Error fetching priority queue: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def get_samples():
    try:
        r = requests.get(f"{API_URL}/samples", params={"limit": 500})
        if r.status_code == 200:
            return pd.DataFrame(r.json())
    except Exception as e:
        st.error(f"Error fetching samples: {e}")
    return pd.DataFrame()

# Title banner
st.title("💧 WaterTriage")
st.markdown("### Data-Driven Water Quality Risk Scoring and Intervention Prioritization (UP & Bihar)")

if not check_api_status():
    st.error("🚨 **API Backend Offline:** The FastAPI service at `http://localhost:8000` could not be reached. Please ensure the backend server is running (`uvicorn app.main:app --reload`).")
    st.stop()

# Load data
df_districts = get_districts()
df_risk = get_risk_scores()
df_priority = get_priority_queue()
df_samples = get_samples()

# Create relationships (District name, State name, and Village name) from synthetic data format
# Let's map village details
# In a real environment, we'd fetch this from database joins. Let's build a quick map for our frontend.
# Let's fetch all samples which contain village metadata, or extract from naming conventions:
# Our seed script created names like "Unnao Village 1", "Araria Village Clean 2", etc.
def parse_village_info(village_id):
    # Fallback mapper
    return {"village_name": f"Village {village_id}", "panchayat_name": f"GP {village_id}", "block_name": "Block 1", "district_name": "Unnao", "state_name": "Uttar Pradesh"}

# Tabs
tab_overview, tab_map, tab_priority = st.tabs(["📊 Overview Dashboard", "🗺️ Geospatial Risk Map", "📋 Intervention Priority Queue"])

with tab_overview:
    st.subheader("Key Performance Indicators (KPIs)")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_districts = len(df_districts) if not df_districts.empty else 0
        st.metric("Districts Monitored", f"{total_districts}", "UP + Bihar")
    with col2:
        total_villages = len(df_risk) if not df_risk.empty else 0
        st.metric("Total Villages Evaluated", f"{total_villages}")
    with col3:
        contaminated_villages = len(df_risk[df_risk["composite_score"] > 0]) if not df_risk.empty else 0
        st.metric("Contaminated Villages", f"{contaminated_villages}", f"{round((contaminated_villages/max(total_villages, 1))*100, 1)}% of total")
    with col4:
        avg_risk = df_risk["composite_score"].mean() if not df_risk.empty else 0.0
        st.metric("Average Risk Score", f"{round(avg_risk, 1)} / 100")

    # Layout for charts
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("#### Severity Band Distribution")
        if not df_risk.empty:
            band_counts = df_risk["severity_band"].value_counts().reindex(["Low", "Medium", "High", "Critical"], fill_value=0)
            # Create a simple colored horizontal bar using Streamlit's native components
            st.bar_chart(band_counts, color="#1f77b4")
        else:
            st.info("No data available.")

    with col_right:
        st.markdown("#### Top Contaminants Detected")
        if not df_risk.empty:
            # Aggregate all contaminants listed in the arrays
            contaminant_list = []
            for plist in df_risk["contaminated_parameters"].dropna():
                contaminant_list.extend(plist)
            
            if contaminant_list:
                s_contaminants = pd.Series(contaminant_list).value_counts()
                st.bar_chart(s_contaminants, color="#d62728")
            else:
                st.info("No contaminants detected.")

    st.markdown("#### District-wise Water Quality Rankings")
    if not df_districts.empty:
        # Display sorted table of districts
        df_disp_dist = df_districts.sort_values(by="average_risk_score", ascending=False).reset_index(drop=True)
        st.dataframe(
            df_disp_dist,
            column_config={
                "id": "District ID",
                "name": "District Name",
                "state_name": "State",
                "total_villages_tested": "Tested Villages",
                "contaminated_villages_count": "Contaminated Villages",
                "average_risk_score": st.column_config.ProgressColumn(
                    "Average Risk Score",
                    help="Mean risk score across all villages",
                    format="%.2f",
                    min_value=0,
                    max_value=100
                ),
            },
            hide_index=True,
            use_container_width=True
        )

with tab_map:
    st.subheader("Geospatial Contamination Mapping")
    st.markdown("The map below overlays evaluated villages. Markers are color-coded by their risk severity bands: **Red (Critical)**, **Orange (High)**, **Yellow (Medium)**, **Green (Low / Compliant)**.")

    if not df_risk.empty:
        # Filter map by severity
        map_filter = st.multiselect(
            "Filter Map by Severity Band",
            options=["Critical", "High", "Medium", "Low"],
            default=["Critical", "High", "Medium"]
        )

        # Base map center: between Bihar & UP
        m = folium.Map(location=[26.0, 82.5], zoom_start=6, tiles="OpenStreetMap")

        # Color map
        color_map = {
            "Critical": "#D32F2F", # Red
            "High": "#F57C00",     # Orange
            "Medium": "#FBC02D",   # Yellow
            "Low": "#388E3C"       # Green
        }

        # Retrieve villages with scores
        # We need to map them to districts to get approximate lat/lons
        # In a production app, the backend would store exact lat/lons. Here we jitter them.
        # We'll use a seed to keep jitters stable
        random.seed(42)

        marker_count = 0
        for idx, row in df_risk.iterrows():
            if row["severity_band"] not in map_filter:
                continue

            # In this frontend, let's extract district name from village name or assume a mock lookup
            # Since names are like "Unnao Village 1", we can parse the district
            v_name = f"Village {row['village_id']}"
            dist_name = "Unnao"
            
            # Simple heuristic mapping for synthetic data
            for d in DISTRICT_COORDS.keys():
                if d in v_name or str(row["village_id"]) == str(idx): # fallback dummy match
                    pass
            
            # Let's search if the village_id can be mapped. Since we seeded it, we know the village id ranges.
            # To make it accurate, let's lookup which district owns this village.
            # Let's map it based on the name of the district we find in the system
            # To do that, we can fetch all samples to find the mapping:
            # Let's fallback to Unnao coordinates if not matched
            district_key = "Unnao"
            
            # Try to infer district from name or samples
            # Let's check our sample cache to find matches
            if not df_samples.empty:
                v_sample = df_samples[df_samples["village_id"] == row["village_id"]]
                if not v_sample.empty:
                    lab = v_sample.iloc[0]["test_lab"]
                    for d in DISTRICT_COORDS.keys():
                        if d in lab:
                            district_key = d
                            break

            center_lat, center_lon = DISTRICT_COORDS.get(district_key, (26.54, 80.49))
            
            # Stable jitter based on village_id
            jitter_lat = (hash(f"lat_{row['village_id']}") % 1000) / 10000.0 - 0.05
            jitter_lon = (hash(f"lon_{row['village_id']}") % 1000) / 10000.0 - 0.05
            lat = center_lat + jitter_lat
            lon = center_lon + jitter_lon

            # Popup text
            contaminants_str = ", ".join(row["contaminated_parameters"]) if row["contaminated_parameters"] else "None"
            recur_str = "Yes" if row["recurring"] else "No"
            
            popup_html = f"""
            <div style="font-family: Arial, sans-serif; font-size: 12px; width: 220px;">
                <b>Village ID:</b> {row['village_id']}<br>
                <b>District:</b> {district_key}<br>
                <b>Composite Score:</b> {row['composite_score']}<br>
                <b>Severity Band:</b> <span style="color: {color_map[row['severity_band']]}; font-weight: bold;">{row['severity_band']}</span><br>
                <b>Contaminants:</b> {contaminants_str}<br>
                <b>Recurring Contamination:</b> {recur_str}<br>
                <b>Last Tested:</b> {row['last_tested']}<br>
            </div>
            """

            folium.CircleMarker(
                location=[lat, lon],
                radius=6 if row["severity_band"] in ["Critical", "High"] else 4,
                color=color_map[row["severity_band"]],
                fill=True,
                fill_color=color_map[row["severity_band"]],
                fill_opacity=0.7,
                popup=folium.Popup(popup_html, max_width=250)
            ).add_to(m)
            marker_count += 1

        st_folium(m, width=1200, height=600)
        st.caption(f"Showing {marker_count} circle markers on map.")
    else:
        st.info("No risk score records available to display on map.")

with tab_priority:
    st.subheader("Intervention Priority Queue")
    st.markdown("This list is sorted by the **Priority Rank** calculated by our decision engine. Villages with critical, recurring, and highly toxic parameters (Arsenic, E. coli, Fluoride) are ranked at the top of the queue.")

    if not df_priority.empty:
        # Filter table by severity or recurrence
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            rec_filter = st.selectbox("Filter by Recurrence", ["All", "Recurring Contamination Only", "Isolated Incidents Only"])
        with col_f2:
            search_query = st.text_input("Search by District / Contaminant (e.g. Katihar, Fluoride)")

        # Merge Priority and Risk data for display
        df_merged = pd.merge(df_priority, df_risk, on="village_id", suffixes=('_priority', '_risk'))
        
        # Add metadata lookup
        # Since we want to display district name and state name
        # We can extract it from the priority reason or test lab using df_samples
        village_to_district = {}
        village_to_state = {}
        if not df_samples.empty:
            for _, s_row in df_samples.iterrows():
                v_id = s_row["village_id"]
                lab = s_row["test_lab"]
                # Infer district
                for d in DISTRICT_COORDS.keys():
                    if d in lab:
                        village_to_district[v_id] = d
                        # Check state
                        if d in ["Katihar", "Araria"]:
                            village_to_state[v_id] = "Bihar"
                        else:
                            village_to_state[v_id] = "Uttar Pradesh"
                        break

        df_merged["District"] = df_merged["village_id"].map(lambda x: village_to_district.get(x, "Unknown"))
        df_merged["State"] = df_merged["village_id"].map(lambda x: village_to_state.get(x, "Unknown"))
        df_merged["Village"] = df_merged["village_id"].map(lambda x: f"Village #{x}")

        # Apply filters
        if rec_filter == "Recurring Contamination Only":
            df_merged = df_merged[df_merged["recurring"] == True]
        elif rec_filter == "Isolated Incidents Only":
            df_merged = df_merged[df_merged["recurring"] == False]

        if search_query:
            q = search_query.lower()
            df_merged = df_merged[
                df_merged["District"].str.lower().str.contains(q) |
                df_merged["reason"].str.lower().str.contains(q) |
                df_merged["intervention_type"].str.lower().str.contains(q)
            ]

        # Clean table
        df_display_priority = df_merged[[
            "priority_rank", "State", "District", "Village", 
            "composite_score", "severity_band", "recurring", 
            "intervention_type", "reason"
        ]].sort_values(by="priority_rank").reset_index(drop=True)

        st.dataframe(
            df_display_priority,
            column_config={
                "priority_rank": "Rank",
                "State": "State",
                "District": "District",
                "Village": "Village Name",
                "composite_score": "Risk Score",
                "severity_band": "Severity",
                "recurring": "Recurring?",
                "intervention_type": "Recommended Intervention",
                "reason": "Detailed Scientific Reason"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No priority recommendations available.")
