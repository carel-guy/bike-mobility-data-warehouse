import streamlit as st
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh

from streamlit_helpers import (
    load_station_data,
    get_latest_snapshot,
    compute_clusters,
    compute_most_active,
    peak_hour_analysis,
    activity_ranking,
)


# Auto-refresh every 45 seconds
st_autorefresh(interval=45000, key="auto_refresh")


st.set_page_config(
    page_title="Bordeaux Bike Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("🚲 Bordeaux Bike Activity – Live Dashboard")

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load DB data
df = load_station_data()
snapshot = get_latest_snapshot(df)

# Filters
with st.sidebar:
    st.header("Filters")
    min_bikes = st.slider("Minimum available bikes", 0, 20, 0)


snapshot = snapshot[snapshot["free_bikes"] >= min_bikes]

# ------------- KPIs -------------
col1, col2, col3 = st.columns(3)

col1.metric("Total Stations", len(snapshot))
col2.metric("Total Bikes Now", int(snapshot["free_bikes"].sum()))
top_station, movement = compute_most_active(df)
col3.metric("Most Active (30min)", f"{top_station}", f"{int(movement)} moves")

st.divider()

# ------------- Map View -------------
st.subheader("🗺️ Live Map of Bordeaux Bike Stations")

view_mode = st.radio(
    "Map View",
    ["Stations", "Clusters", "Both"],
    horizontal=True,
)

# Compute clusters
clustered_df, centers = compute_clusters(snapshot.copy(), n_clusters=10)

# Base map style
MAP_STYLE = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png"


layers = []

# Stations layer
if view_mode in ["Stations", "Both"]:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=snapshot,
            get_position=["longitude", "latitude"],
            get_color="[50, 100, 200, 180]",
            get_radius=25,
            pickable=True,
        )
    )

# Cluster centers layer
if view_mode in ["Clusters", "Both"]:
    cluster_df = []
    for i, (lat, lon) in enumerate(centers):
        cluster_df.append({"lat": lat, "lon": lon, "cluster": i})

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=cluster_df,
            get_position=["lon", "lat"],
            get_color="[255, 100, 50, 220]",
            get_radius=80,
            pickable=True,
        )
    )

# Render map
st.pydeck_chart(
    pdk.Deck(
        map_style=MAP_STYLE,
        initial_view_state=pdk.ViewState(
            latitude=44.8378,
            longitude=-0.5792,
            zoom=12.5,
            pitch=45,
        ),
        layers=layers,
        tooltip={"text": "Station: {name}\nFree Bikes: {free_bikes}"},
    )
)

st.divider()

# ------------- Charts -------------
st.subheader("📊 Analytics")

colA, colB = st.columns(2)

with colA:
    st.plotly_chart(peak_hour_analysis(df), use_container_width=True)

with colB:
    st.plotly_chart(activity_ranking(df), use_container_width=True)

st.success("Dashboard updated ✔")
