from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from backend.app.core.compat import model_to_dict
from backend.app.core.config import config_value, repo_path
from backend.app.db.models import OperatorAlert, VehicleState


DB_PATH = repo_path(config_value("data", "database", default="data/loadsense_demo.sqlite"))
CEBU_ROUTES_PATH = repo_path("data/cebu_osm_routes.geojson")


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
        _seed_cebu_routes_if_needed(conn)


def _seed_cebu_routes_if_needed(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS count FROM routes").fetchone()
    route_count = int(row["count"] if row else 0)
    cebu_count = conn.execute(
        "SELECT COUNT(*) AS count FROM routes WHERE polyline_json LIKE '%10.%' AND polyline_json LIKE '%123.%'"
    ).fetchone()["count"]
    if route_count and cebu_count:
        return
    routes = _load_cebu_geojson_routes()
    if not routes:
        return
    conn.execute("DELETE FROM routes")
    for route in routes:
        conn.execute(
            "INSERT OR REPLACE INTO routes (route, name, polyline_json) VALUES (?, ?, ?)",
            (route["route"], route["name"], json.dumps(route["polyline"])),
        )


def _load_cebu_geojson_routes(max_points: int = 160) -> list[dict[str, Any]]:
    if not CEBU_ROUTES_PATH.exists():
        return []
    try:
        payload = json.loads(CEBU_ROUTES_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    routes: list[dict[str, Any]] = []
    for index, feature in enumerate(payload.get("features", [])):
        props = feature.get("properties", {})
        geometry = feature.get("geometry", {})
        if geometry.get("type") != "LineString":
            continue
        route_id = str(props.get("route_id") or props.get("route") or f"CEBU-{index + 1}").strip()
        name = str(props.get("route_name") or props.get("name") or route_id).strip()
        points = [
            (float(lat), float(lon))
            for lon, lat, *_ in geometry.get("coordinates", [])
            if 10.0 <= float(lat) <= 10.6 and 123.6 <= float(lon) <= 124.1
        ]
        points = _sample_polyline(points, max_points=max_points)
        if route_id and name and len(points) >= 2:
            routes.append({"route": route_id, "name": name, "polyline": points})
    return routes


def _sample_polyline(points: list[tuple[float, float]], max_points: int) -> list[tuple[float, float]]:
    if len(points) <= max_points:
        return points
    sampled: list[tuple[float, float]] = []
    last_index = len(points) - 1
    for i in range(max_points):
        sampled.append(points[round((i / (max_points - 1)) * last_index)])
    result: list[tuple[float, float]] = []
    for point in sampled:
        if not result or point != result[-1]:
            result.append(point)
    return result


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


def save_operator_feedback(alert_id: str, vehicle_id: str, route: str, action: str, timestamp: str) -> None:
    init_db()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO operator_feedback (alert_id, vehicle_id, route, action, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (alert_id, vehicle_id, route, action, timestamp),
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


def route_exists(route: str) -> bool:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT 1 FROM routes WHERE route = ?", (route,)).fetchone()
    return row is not None


def route_name_exists(name: str, exclude_route: str | None = None) -> bool:
    init_db()
    sql = "SELECT route FROM routes WHERE lower(name) = lower(?)"
    params: tuple[Any, ...] = (name,)
    if exclude_route:
        sql += " AND route <> ?"
        params = (name, exclude_route)
    with _connect() as conn:
        row = conn.execute(sql, params).fetchone()
    return row is not None


def load_route_polyline(route: str) -> list[tuple[float, float]]:
    init_db()
    with _connect() as conn:
        row = conn.execute("SELECT polyline_json FROM routes WHERE route = ?", (route,)).fetchone()
    if row is None:
        return []
    try:
        points = json.loads(row["polyline_json"]) if row["polyline_json"] else []
    except Exception:
        return []
    return [(float(lat), float(lon)) for lat, lon in points]


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
        stops = _display_stops(poly, row["name"])
        result.append({
            "route": row["route"],
            "name": row["name"],
            "polyline": [{"latitude": float(lat), "longitude": float(lon)} for lat, lon in poly],
            "stops": stops,
        })
    return result


def _display_stops(poly: list[list[float]] | list[tuple[float, float]], name: str) -> list[dict[str, Any]]:
    if not poly:
        return []
    if len(poly) <= 8:
        indexes = list(range(len(poly)))
    else:
        indexes = sorted({0, len(poly) - 1, *[round((len(poly) - 1) * ratio) for ratio in (0.2, 0.35, 0.5, 0.65, 0.8)]})
    labels = ["Origin", "Checkpoint 1", "Checkpoint 2", "Mid-route", "Checkpoint 3", "Checkpoint 4", "Terminal"]
    stops = []
    for display_index, point_index in enumerate(indexes):
        lat, lon = poly[point_index]
        label = labels[min(display_index, len(labels) - 1)]
        stops.append({
            "stop_id": point_index,
            "name": f"{name} {label}",
            "latitude": float(lat),
            "longitude": float(lon),
        })
    return stops


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
