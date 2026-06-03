import json
import math
import os
import random
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

DB_PATH = os.getenv("LOADSENSE_DB", os.path.join(os.path.dirname(__file__), "loadsense.db"))

ROUTES = [
    {
        "id": "ayala-sm-carbon",
        "name": "Ayala-SM-Carbon",
        "stops": [
            {"id": "ayala", "name": "Ayala Center Cebu", "lat": 10.3181, "lon": 123.9052},
            {"id": "sm-cebu", "name": "SM City Cebu", "lat": 10.3112, "lon": 123.9187},
            {"id": "carbon", "name": "Carbon Market", "lat": 10.2947, "lon": 123.9018},
        ],
        "waypoints": [[10.3181, 123.9052], [10.3157, 123.9004], [10.3112, 123.9187], [10.3056, 123.9141], [10.2947, 123.9018], [10.3036, 123.8951], [10.3181, 123.9052]],
    },
    {
        "id": "colon-talamban",
        "name": "Colon-Talamban",
        "stops": [
            {"id": "colon", "name": "Colon Street", "lat": 10.2969, "lon": 123.8994},
            {"id": "it-park", "name": "Cebu IT Park", "lat": 10.3302, "lon": 123.9067},
            {"id": "talamban", "name": "Talamban", "lat": 10.3706, "lon": 123.9124},
        ],
        "waypoints": [[10.2969, 123.8994], [10.3164, 123.9049], [10.3302, 123.9067], [10.3485, 123.9092], [10.3706, 123.9124]],
    },
    {
        "id": "basak-pardo",
        "name": "Basak-Pardo",
        "stops": [
            {"id": "basak", "name": "Basak", "lat": 10.2899, "lon": 123.8617},
            {"id": "mambaling", "name": "Mambaling", "lat": 10.2914, "lon": 123.8819},
            {"id": "pardo", "name": "Pardo", "lat": 10.2747, "lon": 123.8571},
        ],
        "waypoints": [[10.2899, 123.8617], [10.2914, 123.8819], [10.2841, 123.8721], [10.2747, 123.8571]],
    },
]


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS routes (id TEXT PRIMARY KEY, name TEXT NOT NULL, waypoints_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS stops (id TEXT PRIMARY KEY, route_id TEXT NOT NULL, name TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS vehicles (id TEXT PRIMARY KEY, route_id TEXT NOT NULL, label TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id TEXT NOT NULL, route_id TEXT NOT NULL, timestamp TEXT NOT NULL,
            passenger_count INTEGER NOT NULL, occupancy_tier TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL,
            speed_kph REAL NOT NULL, heading_deg REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS occupancy_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, route_id TEXT NOT NULL, ds TEXT NOT NULL, occupancy REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, vehicle_id TEXT NOT NULL, anomaly_type TEXT NOT NULL,
            timestamp TEXT NOT NULL, status TEXT NOT NULL, details TEXT NOT NULL
        );
        """)


def seed_if_needed():
    init_db()
    with connect() as conn:
        if conn.execute("SELECT COUNT(*) AS count FROM routes").fetchone()["count"]:
            return
        random.seed(42)
        for route in ROUTES:
            conn.execute("INSERT INTO routes VALUES (?, ?, ?)", (route["id"], route["name"], json.dumps(route["waypoints"])))
            for stop in route["stops"]:
                conn.execute("INSERT INTO stops VALUES (?, ?, ?, ?, ?)", (stop["id"], route["id"], stop["name"], stop["lat"], stop["lon"]))
            for i in range(1, 6):
                conn.execute("INSERT INTO vehicles VALUES (?, ?, ?)", (f"{route['id'][:2].upper()}-{i:03d}", route["id"], f"{route['name']} Unit {i}"))
        start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0) - timedelta(days=90)
        for route in ROUTES:
            for hour in range(90 * 24):
                ds = start + timedelta(hours=hour)
                morning = 8 * math.exp(-((ds.hour - 7) ** 2) / 5)
                evening = 9 * math.exp(-((ds.hour - 17.5) ** 2) / 5)
                occupancy = max(0, min(16, 4 + morning + evening + random.uniform(-1.5, 1.5)))
                conn.execute("INSERT INTO occupancy_logs (route_id, ds, occupancy) VALUES (?, ?, ?)", (route["id"], ds.isoformat(), round(occupancy, 2)))


def rows(query, params=()):
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, params).fetchall()]


def row(query, params=()):
    with connect() as conn:
        result = conn.execute(query, params).fetchone()
        return dict(result) if result else None


def execute(query, params=()):
    with connect() as conn:
        return conn.execute(query, params).lastrowid
