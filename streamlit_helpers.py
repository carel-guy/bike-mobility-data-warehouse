import sqlite3
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
from sklearn.cluster import KMeans

from utils.db import DB_PATH



# -------------------------
# Load station activity
# -------------------------
def load_station_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM station_activity", conn)
    conn.close()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


# -------------------------
# Latest snapshot
# -------------------------
def get_latest_snapshot(df):
    if df.empty:
        return df

    df_sorted = df.sort_values(["station_id", "timestamp"])
    snapshot = df_sorted.groupby("station_id", group_keys=False).tail(1)
    return snapshot.reset_index(drop=True)


# -------------------------
# K-Means clustering for map
# -------------------------
def compute_clusters(df, n_clusters=None):
    df = df.copy()

    if df.empty:
        df["cluster"] = pd.Series(dtype=int)
        return df, []

    # Fallback to a sensible default and clamp to available samples
    default_clusters = 10
    if n_clusters is None or n_clusters < 1:
        n_clusters = default_clusters
    n_clusters = min(n_clusters, len(df))

    coords = df[["latitude", "longitude"]]
    kmeans = KMeans(n_clusters=n_clusters, n_init="auto")
    df["cluster"] = kmeans.fit_predict(coords)
    centers = kmeans.cluster_centers_
    return df, centers


# -------------------------
# KPI: Most active station (last 30 min)
# -------------------------
def compute_most_active(df):
    if df.empty:
        return None, 0

    cutoff = pd.Timestamp.now(tz="UTC") - timedelta(minutes=30)
    last30 = df[df["timestamp"] >= cutoff]
    if last30.empty:
        return None, 0

    activity = (
        last30.sort_values(["station_id", "timestamp"])
        .groupby("station_id")["free_bikes"]
        .diff()
        .abs()
        .fillna(0)
    )

    total = activity.groupby(last30["station_id"]).sum().sort_values(ascending=False)

    if total.empty:
        return None, 0

    top_station_id = total.index[0]
    station_names = last30.loc[last30["station_id"] == top_station_id, "name"]
    top_station_name = station_names.mode().iloc[0] if not station_names.empty else str(top_station_id)
    movement = total.iloc[0]
    return top_station_name, movement


# -------------------------
# Filtering helpers
# -------------------------
def filter_by_time(df, hours):
    if hours is None:
        return df

    cutoff = pd.Timestamp.now(tz="UTC") - timedelta(hours=hours)
    return df[df["timestamp"] >= cutoff]


# -------------------------
# KPI helpers
# -------------------------
def compute_capacity_metrics(snapshot):
    if snapshot.empty:
        return {
            "total_bikes": 0,
            "total_docks": 0,
            "total_capacity": 0,
            "utilization": 0.0,
        }

    total_bikes = int(snapshot["free_bikes"].sum())
    total_docks = int(snapshot["empty_slots"].sum())
    total_capacity = total_bikes + total_docks
    util = total_bikes / total_capacity if total_capacity else 0

    return {
        "total_bikes": total_bikes,
        "total_docks": total_docks,
        "total_capacity": total_capacity,
        "utilization": util,
    }


# -------------------------
# Charts
# -------------------------
def citywide_trend_chart(df, freq="15min"):
    if df.empty:
        return px.line(title="No data available")

    trend = (
        df.set_index("timestamp")
        .sort_index()
        .resample(freq)[["free_bikes", "empty_slots"]]
        .sum()
        .reset_index()
    )

    melted = trend.melt(id_vars="timestamp", var_name="metric", value_name="value")
    fig = px.line(
        melted,
        x="timestamp",
        y="value",
        color="metric",
        title="📈 Tendance globale du parc",
        labels={"timestamp": "", "value": "Vélos"},
        color_discrete_map={
            "free_bikes": "#1f77b4",
            "empty_slots": "#aac9e6",
        },
    )
    fig.update_traces(mode="lines+markers")
    fig.update_layout(
        legend_title_text="",
        margin=dict(l=10, r=10, t=50, b=20),
        hovermode="x unified",
    )
    return fig


def utilization_distribution_chart(snapshot):
    if snapshot.empty:
        return px.histogram(title="No station snapshot data")

    snapshot = snapshot.copy()
    capacity = snapshot["free_bikes"] + snapshot["empty_slots"]
    snapshot["utilization_pct"] = np.where(
        capacity > 0, snapshot["free_bikes"] / capacity, 0
    )

    fig = px.histogram(
        snapshot,
        x="utilization_pct",
        nbins=20,
        title="📊 Répartition de la disponibilité",
        labels={"utilization_pct": "Part de vélos disponibles"},
        color_discrete_sequence=["#1f77b4"],
    )
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=20))
    fig.update_xaxes(tickformat="%", range=[0, 1])
    return fig


def station_utilization_chart(snapshot, limit=10):
    if snapshot.empty:
        return px.bar(title="No station data to rank")

    ranked = snapshot.copy()
    ranked["capacity"] = ranked["free_bikes"] + ranked["empty_slots"]
    ranked = ranked[ranked["capacity"] > 0]
    if ranked.empty:
        return px.bar(title="Stations missing capacity information")

    ranked["utilization_pct"] = ranked["free_bikes"] / ranked["capacity"]
    top = ranked.sort_values("utilization_pct", ascending=False).head(limit)

    fig = px.bar(
        top,
        x="name",
        y="utilization_pct",
        title=f"🥇 Top {len(top)} stations par disponibilité",
        labels={"name": "", "utilization_pct": "Vélos disponibles"},
        color="utilization_pct",
        color_continuous_scale="Blues",
    )
    fig.update_layout(
        margin=dict(l=10, r=10, t=50, b=40),
        xaxis_tickangle=-30,
        coloraxis_showscale=False,
    )
    fig.update_yaxes(tickformat="%")
    return fig


def weekday_hour_heatmap(df):
    if df.empty:
        return px.imshow([[0]], title="🕒 Chaleur disponibilité (jour × heure) – aucune donnée")

    enriched = df.copy()
    enriched["weekday"] = enriched["timestamp"].dt.day_name()
    enriched["weekday_order"] = enriched["timestamp"].dt.weekday
    enriched["hour"] = enriched["timestamp"].dt.hour

    heat = (
        enriched.groupby(["weekday", "weekday_order", "hour"])["free_bikes"]
        .mean()
        .reset_index()
    )

    ordered_days = (
        heat[["weekday", "weekday_order"]]
        .drop_duplicates()
        .sort_values("weekday_order")["weekday"]
        .tolist()
    )

    pivot = (
        heat.pivot(index="weekday", columns="hour", values="free_bikes")
        .reindex(ordered_days)
        .fillna(0)
    )

    fig = px.imshow(
        pivot,
        aspect="auto",
        color_continuous_scale="Blues",
        labels=dict(x="Heure de la journée", y="", color="Vélos moyens"),
        title="🕒 Chaleur disponibilité (jour × heure)",
    )
    fig.update_layout(margin=dict(l=10, r=20, t=60, b=20))
    return fig


def capacity_donut_chart(snapshot):
    metrics = compute_capacity_metrics(snapshot)
    total = metrics["total_bikes"] + metrics["total_docks"]
    if total == 0:
        return px.pie(
            names=["Vélos", "Bornes"],
            values=[0, 0],
            hole=0.6,
            title="🍩 Répartition vélos / bornes",
        )

    fig = px.pie(
        names=["Vélos disponibles", "Bornes libres"],
        values=[metrics["total_bikes"], metrics["total_docks"]],
        hole=0.6,
        title="🍩 Répartition vélos / bornes",
        color_discrete_sequence=["#1f77b4", "#ccdffc"],
    )
    fig.update_traces(textinfo="percent+label")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10))
    return fig


# -------------------------
# Additional tables & charts
# -------------------------
def net_change_chart(df, freq="30min"):
    if df.empty:
        return px.bar(title="📉 Variation nette des vélos (aucune donnée)")

    totals = (
        df.set_index("timestamp")
        .sort_index()
        .resample(freq)["free_bikes"]
        .sum()
        .rename("total_bikes")
    )

    changes = totals.diff().fillna(0)
    chart_df = pd.DataFrame(
        {
            "timestamp": totals.index,
            "change": changes,
        }
    )
    chart_df["direction"] = np.where(chart_df["change"] >= 0, "Increase", "Decrease")

    fig = px.bar(
        chart_df,
        x="timestamp",
        y="change",
        color="direction",
        title="📉 Variation nette des vélos",
        labels={"change": "Δ vélos", "timestamp": ""},
        color_discrete_map={"Increase": "#1f9e89", "Decrease": "#d64f4f"},
    )
    fig.update_layout(showlegend=False, margin=dict(l=10, r=10, t=50, b=20))
    fig.update_yaxes(zeroline=True, zerolinecolor="#ddd")
    return fig


def station_activity_table(df, limit=15):
    if df.empty:
        return pd.DataFrame(
            columns=[
                "station_id",
                "name",
                "records",
                "avg_bikes",
                "avg_empty_slots",
                "total_moves",
                "turnover_rate",
            ]
        )

    ordered = df.sort_values(["station_id", "timestamp"])
    ordered["movement"] = ordered.groupby("station_id")["free_bikes"].diff().abs()
    ordered["movement"] = ordered["movement"].fillna(0)

    summary = (
        ordered.groupby(["station_id", "name"])
        .agg(
            records=("timestamp", "count"),
            avg_bikes=("free_bikes", "mean"),
            avg_empty_slots=("empty_slots", "mean"),
            total_moves=("movement", "sum"),
        )
        .reset_index()
    )

    summary["turnover_rate"] = summary["total_moves"] / summary["records"].clip(lower=1)
    summary = summary.sort_values("total_moves", ascending=False)

    columns = [
        "station_id",
        "name",
        "records",
        "avg_bikes",
        "avg_empty_slots",
        "total_moves",
        "turnover_rate",
    ]
    summary = summary[columns].head(limit)
    summary["avg_bikes"] = summary["avg_bikes"].round(1)
    summary["avg_empty_slots"] = summary["avg_empty_slots"].round(1)
    summary["turnover_rate"] = summary["turnover_rate"].round(2)
    summary["total_moves"] = summary["total_moves"].round(0).astype(int)
    return summary


def top_station_trend_chart(df, limit=3):
    if df.empty:
        return px.line(title="📍 Evolution des stations (aucune donnée)")

    leaderboard = station_activity_table(df, limit=limit)
    if leaderboard.empty:
        return px.line(title="📍 Evolution des stations (aucune donnée)")

    top_ids = leaderboard["station_id"].tolist()
    subset = (
        df[df["station_id"].isin(top_ids)]
        .sort_values("timestamp")
        .copy()
    )

    fig = px.line(
        subset,
        x="timestamp",
        y="free_bikes",
        color="name",
        title="📍 Evolution des stations les plus actives",
        markers=True,
    )
    fig.update_layout(
        legend_title_text="Station",
        margin=dict(l=10, r=10, t=50, b=20),
    )
    return fig


def prepare_snapshot_table(snapshot):
    if snapshot.empty:
        return pd.DataFrame(
            columns=[
                "station_id",
                "name",
                "free_bikes",
                "empty_slots",
                "capacity",
                "utilization_pct",
            ]
        )

    snapshot = snapshot.copy()
    snapshot["capacity"] = snapshot["free_bikes"] + snapshot["empty_slots"]
    snapshot["capacity"] = snapshot["capacity"].replace(0, 1)
    snapshot["utilization_pct"] = snapshot["free_bikes"] / snapshot["capacity"]
    return snapshot


# -------------------------
# Peak Hours
# -------------------------
def peak_hour_analysis(df):
    df["hour"] = df["timestamp"].dt.hour
    hourly = df.groupby("hour")["free_bikes"].mean().reset_index()
    fig = px.line(hourly, x="hour", y="free_bikes", title="Bike Usage by Hour")
    return fig


# -------------------------
# Activity Ranking
# -------------------------
def activity_ranking(df):
    df_sorted = df.sort_values(["station_id", "timestamp"])
    df_sorted["movement"] = df_sorted.groupby("station_id")["free_bikes"].diff().abs()

    ranking = (
        df_sorted.groupby(["station_id", "name"])["movement"]
        .sum()
        .reset_index()
        .sort_values("movement", ascending=False)
    )

    fig = px.bar(
        ranking.head(10),
        x="name",
        y="movement",
        title="🏆 Top 10 des stations les plus actives",
    )

    return fig
