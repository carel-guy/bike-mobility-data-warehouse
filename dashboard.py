import math

import pydeck as pdk
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from streamlit_helpers import (
    activity_ranking,
    citywide_trend_chart,
    capacity_donut_chart,
    critical_split_donut,
    compute_capacity_metrics,
    compute_most_active,
    filter_by_time,
    detect_static_bikes,
    get_latest_snapshot,
    load_station_data,
    net_change_chart,
    prepare_snapshot_table,
    station_activity_table,
    station_health_scatter,
    station_history_chart,
    top_station_trend_chart,
    turnover_vs_capacity_chart,
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

ANOMALY_WINDOW_MINUTES = 15
ANOMALY_ACTIVITY_THRESHOLD = 5
ANOMALY_STATIC_THRESHOLD = 1

if history_df.empty:
    anomalies_df = None
else:
    anomalies_df = detect_static_bikes(
        history_df,
        window_minutes=ANOMALY_WINDOW_MINUTES,
        activity_threshold=ANOMALY_ACTIVITY_THRESHOLD,
        static_threshold=ANOMALY_STATIC_THRESHOLD,
    )

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
    donut_col1, donut_col2 = st.columns(2)
    donut_col1.plotly_chart(
        capacity_donut_chart(snapshot_table),
        width="stretch",
    )
    donut_col2.plotly_chart(
        critical_split_donut(snapshot_table, critical_threshold),
        width="stretch",
    )

st.divider()

# ------------- Map -------------
st.subheader("🗺️ Carte interactive des stations")
if snapshot_table.empty:
    st.info("Aucune donnée de localisation disponible pour ce snapshot.")
else:
    map_df = snapshot_table.copy()
    map_df["capacity"] = (map_df["free_bikes"] + map_df["empty_slots"]).replace(0, 1)
    map_df["utilization_pct"] = map_df["free_bikes"] / map_df["capacity"]
    map_df["radius"] = map_df["capacity"].clip(1, 20) * 1.0

    def color_from_util(pct):
        pct = max(0, min(1, pct))
        r = int(220 - 150 * pct)
        g = int(60 + 150 * pct)
        b = int(50 + 80 * pct)
        return [r, g, b, 230]

    map_df["color"] = map_df["utilization_pct"].apply(color_from_util)
    center_lat = float(map_df["latitude"].mean())
    center_lon = float(map_df["longitude"].mean())

    tile_layer = pdk.Layer(
        "TileLayer",
        data=None,
        get_tile_url="https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
        tile_size=256,
    )

    stations_layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_df,
        get_position=["longitude", "latitude"],
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        radius_units="meters",
        stroked=True,
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        opacity=0.85,
    )

    tooltip = {
        "html": "Station: <b>{name}</b><br/>Vélos: {free_bikes}<br/>Bornes: {empty_slots}",
        "style": {"color": "white", "font-size": "13px"},
    }

    st.pydeck_chart(
        pdk.Deck(
            layers=[tile_layer, stations_layer],
            initial_view_state=pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=12.5,
                pitch=45,
            ),
            tooltip=tooltip,
        )
    )

    st.markdown(
        """
        <div class="map-legend">
            <span class="legend-title">Disponibilité</span>
            <div class="legend-scale">
                <span><i style="background: rgb(220,60,50);"></i>Faible</span>
                <span><i style="background: rgb(135,135,85);"></i>Moyenne</span>
                <span><i style="background: rgb(70,210,130);"></i>Confort</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()

# ------------- Citywide monitoring -------------
st.subheader("📈 Indicateurs globaux")
if history_df.empty:
    st.info("Aucune donnée historique dans la fenêtre sélectionnée.")
else:
    trend_col, change_col = st.columns(2)
    trend_col.plotly_chart(citywide_trend_chart(history_df), width="stretch")
    change_col.plotly_chart(net_change_chart(history_df), width="stretch")

dist_col, heat_col = st.columns(2)
dist_col.plotly_chart(
    utilization_distribution_chart(snapshot_table), width="stretch"
)
if history_df.empty:
    heat_col.info("La carte de chaleur nécessite des données historiques.")
else:
    heat_col.plotly_chart(weekday_hour_heatmap(history_df), width="stretch")

if not history_df.empty:
    st.plotly_chart(
        top_station_trend_chart(history_df, limit=min(5, top_n)),
        width="stretch",
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
        height=360,
    )

st.divider()

# ------------- Station search -------------
st.subheader("🔎 Recherche de station")
if snapshot_table.empty:
    st.info("Aucune station disponible dans le snapshot actuel.")
else:
    station_names = sorted(snapshot_table["name"].unique())
    search_query = st.text_input("Rechercher une station par nom", "")
    if search_query:
        filtered_names = [n for n in station_names if search_query.lower() in n.lower()]
    else:
        filtered_names = station_names

    if not filtered_names:
        st.warning("Aucune station ne correspond à cette recherche.")
    else:
        selected_station = st.selectbox(
            "Sélectionnez une station",
            filtered_names,
            key="station_search_select",
        )
        station_snapshot = snapshot_table[snapshot_table["name"] == selected_station].iloc[0]
        station_id = station_snapshot["station_id"]
        if (
            anomalies_df is not None
            and not anomalies_df.empty
            and station_id in anomalies_df["station_id"].values
        ):
            st.markdown(
                "<div class='badge-alert'>🛠️ Station signalée : vélos potentiellement bloqués</div>",
                unsafe_allow_html=True,
            )
        capacity = station_snapshot["free_bikes"] + station_snapshot["empty_slots"]
        util_pct = (
            station_snapshot["free_bikes"] / capacity if capacity else 0
        )

        info_cols = st.columns(4)
        info_cols[0].metric("Vélos disponibles", int(station_snapshot["free_bikes"]))
        info_cols[1].metric("Bornes libres", int(station_snapshot["empty_slots"]))
        info_cols[2].metric("Capacité", int(capacity))
        info_cols[3].metric("Disponibilité", f"{util_pct:.0%}")

        if history_df.empty:
            st.info("Aucun historique pour la fenêtre choisie.")
        else:
            history_station = (
                history_df[history_df["name"] == selected_station]
                .sort_values("timestamp")
            )
            if history_station.empty:
                st.info(
                    "Pas de mesures enregistrées pour cette station sur la période sélectionnée."
                )
            else:
                below_share = float(
                    (history_station["free_bikes"] <= critical_threshold).mean()
                )
                above_share = max(0.0, 1 - below_share)
                share_cols = st.columns(2)
                share_cols[0].metric(
                    "Temps sous le seuil",
                    f"{below_share * 100:.0f}%",
                )
                share_cols[1].metric(
                    "Temps au-dessus du seuil",
                    f"{above_share * 100:.0f}%",
                )

                st.plotly_chart(
                    station_history_chart(history_station, selected_station),
                    width="stretch",
                )
                recent_history = (
                    history_station.sort_values("timestamp", ascending=False).head(20)
                )
                st.dataframe(
                    recent_history[
                        ["timestamp", "free_bikes", "empty_slots"]
                    ].set_index("timestamp"),
                    height=300,
                )

st.divider()

# ------------- Additional visuals -------------
st.subheader("🎨 Visualisations complémentaires")
vis_col1, vis_col2 = st.columns(2)
if snapshot_table.empty:
    vis_col1.info("Aucune donnée de snapshot pour afficher la santé des stations.")
else:
    vis_col1.plotly_chart(
        station_health_scatter(snapshot_table, critical_threshold),
        width="stretch",
    )

if history_df.empty:
    vis_col2.info("Le graphique de turn-over nécessite un historique.")
else:
    vis_col2.plotly_chart(
        turnover_vs_capacity_chart(history_df, limit=max(10, top_n)),
        width="stretch",
    )

st.divider()

# ------------- Broken bike detection -------------
st.subheader("🚨 Suspicion de vélos défectueux")
if anomalies_df is None:
    st.info("Sélectionnez une fenêtre historique plus large pour activer l'analyse.")
else:
    if anomalies_df.empty:
        st.success("Aucune station active ne présente de vélos potentiellement bloqués.")
    else:
        st.warning(
            "Certaines stations restent actives mais leur stock ne bouge plus : vigilance maintenance."
        )
        anomaly_snapshot = snapshot_table[["station_id", "free_bikes", "empty_slots"]]
        anomalies = anomalies_df.merge(
            anomaly_snapshot, on="station_id", how="left"
        )
        anomalies.rename(
            columns={
                "total_movement": "Mouvements (fenêtre)",
                "recent_min": "Min réc.",
                "recent_max": "Max réc.",
                "recent_range": "Amplitude",
                "sample_count": "Échantillons",
                "free_bikes": "Vélos actuels",
                "empty_slots": "Bornes actuelles",
            },
            inplace=True,
        )
        st.dataframe(
            anomalies.set_index("station_id"),
            height=320,
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
    chart_col.plotly_chart(activity_ranking(history_df), width="stretch")
    table_col.markdown("##### Tableau des mouvements")
    table_col.dataframe(
        leaderboard_df.set_index("station_id"),
        height=420,
    )

st.success("Tableau de bord mis à jour ✔")
