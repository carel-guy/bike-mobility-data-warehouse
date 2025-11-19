import sqlite3
import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px
from datetime import datetime, timedelta
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
    last_ts = df["timestamp"].max()
    return df[df["timestamp"] == last_ts]


# -------------------------
# K-Means clustering for map
# -------------------------
def compute_clusters(df, n_clusters=10):
    coords = df[["latitude", "longitude"]]
    kmeans = KMeans(n_clusters=n_clusters, n_init="auto")
    df["cluster"] = kmeans.fit_predict(coords)
    centers = kmeans.cluster_centers_
    return df, centers


# -------------------------
# KPI: Most active station (last 30 min)
# -------------------------
def compute_most_active(df):
    cutoff = datetime.utcnow() - timedelta(minutes=30)
    last30 = df[df["timestamp"] >= cutoff]

    activity = (
        last30.sort_values(["station_id", "timestamp"])
        .groupby("station_id")["free_bikes"]
        .diff()
        .abs()
    )

    total = activity.groupby(df["station_id"]).sum().sort_values(ascending=False)

    if total.empty:
        return None, 0

    top_station = total.index[0]
    movement = total.iloc[0]
    return top_station, movement


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
        title="Top 10 Most Active Stations",
    )

    return fig
