from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from backend.app.core.compat import model_to_dict
from backend.app.core.config import config_value, repo_path
from backend.app.db.models import OperatorAlert, VehicleState


DB_PATH = repo_path(config_value("data", "database", default="data/loadsense_demo.sqlite"))


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS telemetry_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                route TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                occupancy INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                tier TEXT NOT NULL,
                source_timestamp TEXT NOT NULL,
                received_at TEXT NOT NULL,
                eta_minutes REAL NOT NULL,
                eta_source TEXT NOT NULL,
                next_stop_id INTEGER NOT NULL,
                route_deviation_json TEXT NOT NULL,
                signal_quality TEXT NOT NULL,
                speed_kph REAL,
                heading REAL
            );

            CREATE TABLE IF NOT EXISTS vehicle_states (
                vehicle_id TEXT PRIMARY KEY,
                route TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                occupancy INTEGER NOT NULL,
                capacity INTEGER NOT NULL,
                tier TEXT NOT NULL,
                source_timestamp TEXT NOT NULL,
                received_at TEXT NOT NULL,
                eta_minutes REAL NOT NULL,
                eta_source TEXT NOT NULL,
                next_stop_id INTEGER NOT NULL,
                route_deviation_json TEXT NOT NULL,
                signal_quality TEXT NOT NULL,
                speed_kph REAL,
                heading REAL
            );

            CREATE TABLE IF NOT EXISTS operator_alerts (
                id TEXT PRIMARY KEY,
                severity TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                route TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                acknowledged INTEGER NOT NULL DEFAULT 0
            );

            CREATE TABLE IF NOT EXISTS operator_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                vehicle_id TEXT NOT NULL,
                route TEXT NOT NULL,
                action TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS chatbot_queries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                route TEXT NOT NULL,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS routes (
                route TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                polyline_json TEXT NOT NULL
            );
            """
        )
        # seed routes table from config if empty
        cur = conn.execute("SELECT COUNT(*) AS count FROM routes").fetchone()
        if cur and cur["count"] == 0:
            try:
                from backend.app.core.config import config_value

                cfg_routes = config_value("routes", default={})
                for route, details in cfg_routes.items():
                    conn.execute(
                        "INSERT OR REPLACE INTO routes (route, name, polyline_json) VALUES (?, ?, ?)",
                        (route, details.get("name", route), json.dumps(details.get("polyline", []))),
                    )
            except Exception:
                # if seeding fails, continue without raising
                pass


def save_vehicle_state(state: VehicleState, received_at: str) -> None:
    init_db()
    data = model_to_dict(state)
    params = {
        "vehicle_id": state.vehicle_id,
        "route": state.route,
        "latitude": state.latitude,
        "longitude": state.longitude,
        "occupancy": state.occupancy,
        "capacity": state.capacity,
        "tier": state.tier,
        "source_timestamp": state.timestamp,
        "received_at": received_at,
        "eta_minutes": state.eta_minutes,
        "eta_source": state.eta_source,
        "next_stop_id": state.next_stop_id,
        "route_deviation_json": json.dumps(data["route_deviation"]),
        "signal_quality": state.signal_quality,
        "speed_kph": state.speed_kph,
        "heading": state.heading,
    }
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO telemetry_logs (
                vehicle_id, route, latitude, longitude, occupancy, capacity, tier,
                source_timestamp, received_at, eta_minutes, eta_source, next_stop_id,
                route_deviation_json, signal_quality, speed_kph, heading
            ) VALUES (
                :vehicle_id, :route, :latitude, :longitude, :occupancy, :capacity, :tier,
                :source_timestamp, :received_at, :eta_minutes, :eta_source, :next_stop_id,
                :route_deviation_json, :signal_quality, :speed_kph, :heading
            )
            """,
            params,
        )
        conn.execute(
            """
            INSERT INTO vehicle_states (
                vehicle_id, route, latitude, longitude, occupancy, capacity, tier,
                source_timestamp, received_at, eta_minutes, eta_source, next_stop_id,
                route_deviation_json, signal_quality, speed_kph, heading
            ) VALUES (
                :vehicle_id, :route, :latitude, :longitude, :occupancy, :capacity, :tier,
                :source_timestamp, :received_at, :eta_minutes, :eta_source, :next_stop_id,
                :route_deviation_json, :signal_quality, :speed_kph, :heading
            )
            ON CONFLICT(vehicle_id) DO UPDATE SET
                route=excluded.route,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                occupancy=excluded.occupancy,
                capacity=excluded.capacity,
                tier=excluded.tier,
                source_timestamp=excluded.source_timestamp,
                received_at=excluded.received_at,
                eta_minutes=excluded.eta_minutes,
                eta_source=excluded.eta_source,
                next_stop_id=excluded.next_stop_id,
                route_deviation_json=excluded.route_deviation_json,
                signal_quality=excluded.signal_quality,
                speed_kph=excluded.speed_kph,
                heading=excluded.heading
            """,
            params,
        )


def save_alert(alert: OperatorAlert) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT OR IGNORE INTO operator_alerts (
                id, severity, vehicle_id, route, message, timestamp, acknowledged
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                alert.id,
                alert.severity,
                alert.vehicle_id,
                alert.route,
                alert.message,
                alert.timestamp,
                int(alert.acknowledged),
            ),
        )


def acknowledge_alert(alert_id: str, timestamp: str) -> Optional[OperatorAlert]:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT * FROM operator_alerts WHERE id = ?", (alert_id,)).fetchone()
        if row is None:
            return None
        conn.execute("UPDATE operator_alerts SET acknowledged = 1 WHERE id = ?", (alert_id,))
        conn.execute(
            """
            INSERT INTO operator_feedback (alert_id, vehicle_id, route, action, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (alert_id, row["vehicle_id"], row["route"], "verified", timestamp),
        )
    return _alert_from_row(row, acknowledged=True)


def save_chat_query(route: str, query: str, answer: str, timestamp: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chatbot_queries (route, query, answer, timestamp) VALUES (?, ?, ?, ?)",
            (route, query, answer, timestamp),
        )


def load_vehicle_states() -> list[VehicleState]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM vehicle_states").fetchall()
    return [_vehicle_from_row(row) for row in rows]


def load_alerts() -> list[OperatorAlert]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM operator_alerts").fetchall()
    return [_alert_from_row(row) for row in rows]


def list_incidents(limit: int = 50) -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute(
            """
            SELECT id, severity, vehicle_id, route, message, timestamp, acknowledged
            FROM operator_alerts
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) | {"acknowledged": bool(row["acknowledged"])} for row in rows]


def database_status() -> dict[str, Any]:
    init_db()
    with _connect() as conn:
        tables = ["telemetry_logs", "vehicle_states", "operator_alerts", "operator_feedback", "chatbot_queries", "routes"]
        counts = {
            table: conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
            for table in tables
        }
    return {
        "path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "tables": counts,
    }


def save_route(route: str, name: str, polyline: list[tuple[float, float]]):
    init_db()
    with _connect() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO routes (route, name, polyline_json) VALUES (?, ?, ?)",
            (route, name, json.dumps(polyline)),
        )


def load_routes() -> list[dict[str, Any]]:
    init_db()
    with _connect() as conn:
        rows = conn.execute("SELECT route, name, polyline_json FROM routes").fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        try:
            poly = json.loads(row["polyline_json"]) if row["polyline_json"] else []
        except Exception:
            poly = []
        result.append({
            "route": row["route"],
            "name": row["name"],
            "polyline": [{"latitude": float(lat), "longitude": float(lon)} for lat, lon in poly],
            "stops": [{"stop_id": i, "name": f"{row['name']} Stop {i+1}", "latitude": lat, "longitude": lon} for i, (lat, lon) in enumerate(poly)],
        })
    return result


def _vehicle_from_row(row: sqlite3.Row) -> VehicleState:
    return VehicleState(
        vehicle_id=row["vehicle_id"],
        route=row["route"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        occupancy=row["occupancy"],
        capacity=row["capacity"],
        tier=row["tier"],
        timestamp=row["source_timestamp"],
        eta_minutes=row["eta_minutes"],
        eta_source=row["eta_source"],
        next_stop_id=row["next_stop_id"],
        route_deviation=json.loads(row["route_deviation_json"]),
        signal_quality=row["signal_quality"],
        speed_kph=row["speed_kph"],
        heading=row["heading"],
    )


def _alert_from_row(row: sqlite3.Row, acknowledged: Optional[bool] = None) -> OperatorAlert:
    return OperatorAlert(
        id=row["id"],
        severity=row["severity"],
        vehicle_id=row["vehicle_id"],
        route=row["route"],
        message=row["message"],
        timestamp=row["timestamp"],
        acknowledged=bool(row["acknowledged"]) if acknowledged is None else acknowledged,
    )
