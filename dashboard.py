import math

import streamlit as st
from streamlit_autorefresh import st_autorefresh

from streamlit_helpers import (
    activity_ranking,
    citywide_trend_chart,
    capacity_donut_chart,
    compute_capacity_metrics,
    compute_most_active,
    filter_by_time,
    get_latest_snapshot,
    load_station_data,
    net_change_chart,
    prepare_snapshot_table,
    station_activity_table,
    top_station_trend_chart,
    utilization_distribution_chart,
    weekday_hour_heatmap,
)


# Auto-refresh every 45 seconds
st_autorefresh(interval=45000, key="auto_refresh")


st.set_page_config(
    page_title="Bordeaux Bike Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.title("🚲 Observatoire VCUB en temps réel")
st.caption(
    "Supervisez la disponibilité des vélos, les variations d'activité et les stations critiques sur l'ensemble du réseau bordelais."
)

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Load DB data
df = load_station_data()
snapshot = get_latest_snapshot(df)

# Sidebar controls
with st.sidebar:
    st.header("Paramètres d'analyse")
    window_selection = st.selectbox(
        "Fenêtre historique",
        (
            "Dernière heure",
            "Dernières 3 heures",
            "Dernières 6 heures",
            "Dernières 12 heures",
            "Dernières 24 heures",
            "Toutes les données",
        ),
    )
    window_hours = {
        "Dernière heure": 1,
        "Dernières 3 heures": 3,
        "Dernières 6 heures": 6,
        "Dernières 12 heures": 12,
        "Dernières 24 heures": 24,
        "Toutes les données": None,
    }[window_selection]

    top_n = st.slider("Nombre de stations à afficher", 5, 25, 10)
    critical_threshold = st.slider("Seuil critique (≤ vélos disponibles)", 0, 15, 3)


history_df = filter_by_time(df, window_hours)
snapshot_table = prepare_snapshot_table(snapshot)
full_snapshot = snapshot_table.copy()

# ------------- KPIs -------------
metrics = compute_capacity_metrics(snapshot_table)
top_station, movement = compute_most_active(history_df)
critical_count = int((snapshot_table["free_bikes"] <= critical_threshold).sum())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Stations actives", len(snapshot_table))
col2.metric("Vélos disponibles", f"{metrics['total_bikes']:,}")
col3.metric("Bornes libres", f"{metrics['total_docks']:,}")
col4.metric("Disponibilité globale", f"{metrics['utilization']:.0%}")

col5, col6 = st.columns(2)
if top_station:
    col5.metric("Station la plus active (30 min)", top_station, f"{int(movement)} mouvements")
else:
    col5.metric("Station la plus active (30 min)", "—", "0 mouvement")
col6.metric(
    "Stations sous le seuil",
    critical_count,
    help="Nombre de stations au niveau du seuil critique choisi",
)

if not snapshot_table.empty:
    donut_col, _ = st.columns([1.2, 2.8])
    donut_col.plotly_chart(
        capacity_donut_chart(snapshot_table), use_container_width=True
    )

st.divider()

# ------------- Citywide monitoring -------------
st.subheader("📈 Indicateurs globaux")
if history_df.empty:
    st.info("Aucune donnée historique dans la fenêtre sélectionnée.")
else:
    trend_col, change_col = st.columns(2)
    trend_col.plotly_chart(citywide_trend_chart(history_df), use_container_width=True)
    change_col.plotly_chart(net_change_chart(history_df), use_container_width=True)

dist_col, heat_col = st.columns(2)
dist_col.plotly_chart(
    utilization_distribution_chart(snapshot_table), use_container_width=True
)
if history_df.empty:
    heat_col.info("La carte de chaleur nécessite des données historiques.")
else:
    heat_col.plotly_chart(weekday_hour_heatmap(history_df), use_container_width=True)

if not history_df.empty:
    st.plotly_chart(
        top_station_trend_chart(history_df, limit=min(5, top_n)),
        use_container_width=True,
    )

st.divider()

# ------------- Real-time snapshot tables -------------
st.subheader("🛰️ Stations en direct")
sorted_snapshot = snapshot_table.sort_values("free_bikes", ascending=False)
top_available = sorted_snapshot.sort_values("utilization_pct", ascending=False).head(
    top_n
)
critical_table = (
    sorted_snapshot[sorted_snapshot["free_bikes"] <= critical_threshold]
    .sort_values("free_bikes")
    .head(top_n)
)

col_a, col_b = st.columns(2)
col_a.markdown("##### Stations sous le seuil")
if critical_table.empty:
    col_a.success("Toutes les stations sont au-dessus du seuil critique.")
else:
    col_a.dataframe(
        critical_table[
            [
                "station_id",
                "name",
                "free_bikes",
                "empty_slots",
                "utilization_pct",
            ]
        ].set_index("station_id"),
        use_container_width=True,
        height=360,
    )

col_b.markdown("##### Stations les plus disponibles")
if top_available.empty:
    col_b.info("Aucune donnée instantanée disponible.")
else:
    col_b.dataframe(
        top_available[
            [
                "station_id",
                "name",
                "free_bikes",
                "empty_slots",
                "utilization_pct",
            ]
        ].set_index("station_id"),
        use_container_width=True,
        height=360,
    )

st.divider()

# ------------- All stations overview -------------
st.subheader("📋 Toutes les stations VCUB")
st.caption("Visualisez l'inventaire complet issu du dernier relevé.")
if full_snapshot.empty:
    st.warning("Aucune capture n'a encore été enregistrée.")
else:
    page_size = st.selectbox(
        "Taille de page",
        options=[10, 20, 50, 100],
        index=0,
        key="all_stations_page_size",
    )
    total_rows = len(full_snapshot)
    total_pages = max(1, math.ceil(total_rows / page_size))
    page = st.number_input(
        "Page",
        min_value=1,
        max_value=total_pages,
        value=1,
        step=1,
        key="all_stations_page",
    )
    start = (page - 1) * page_size
    end = start + page_size
    page_df = full_snapshot.iloc[start:end]

    st.dataframe(
        page_df[
            [
                "station_id",
                "name",
                "free_bikes",
                "empty_slots",
                "capacity",
                "utilization_pct",
                "latitude",
                "longitude",
            ]
        ].set_index("station_id"),
        use_container_width=True,
        height=420,
    )
    st.caption(f"Page {page}/{total_pages} – {total_rows} stations au total.")

st.divider()

# ------------- Activity insights -------------
st.subheader("⚡ Analyse de l'activité")
if history_df.empty:
    st.info("Sélectionnez une fenêtre historique pour calculer les classements.")
else:
    leaderboard_df = station_activity_table(history_df, limit=top_n)
    chart_col, table_col = st.columns(2)
    chart_col.plotly_chart(activity_ranking(history_df), use_container_width=True)
    table_col.markdown("##### Tableau des mouvements")
    table_col.dataframe(
        leaderboard_df.set_index("station_id"),
        use_container_width=True,
        height=420,
    )

st.success("Tableau de bord mis à jour ✔")
