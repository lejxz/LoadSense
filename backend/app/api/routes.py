import json
import csv
import io
import math
import zipfile
from typing import Any, Optional

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, validator

from backend.app.core.config import default_route, get_config
from backend.app.core.compat import model_to_dict, validate_model
from backend.app.core.phase2 import load_demand_forecast, predict_eta_details
from backend.app.core.routes import list_routes
from backend.app.db import sqlite_store
from backend.app.core.state import fleet_store
from backend.app.db.models import OperatorAlert as OperatorAlertModel
from uuid import uuid4
from datetime import datetime, timezone

router = APIRouter()


class Telemetry(BaseModel):
    vehicle_id: str
    route: str = default_route()
    latitude: float
    longitude: float
    occupancy: int
    timestamp: str
    speed_kph: Optional[float] = None
    heading: Optional[float] = None
    signal_quality: Optional[str] = None


class ChatQuery(BaseModel):
    route: str = default_route()
    query: str


@router.post("/telemetry")
def receive_telemetry(t: Telemetry):
    state = fleet_store.upsert_telemetry(t)
    return {"status": "accepted", "vehicle": model_to_dict(state), "summary": fleet_store.summary()}


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            try:
                payload = validate_model(Telemetry, json.loads(text))
                state = fleet_store.upsert_telemetry(payload)
                await websocket.send_json({"status": "accepted", "vehicle": model_to_dict(state), "summary": fleet_store.summary()})
            except Exception as exc:
                await websocket.send_json({"status": "error", "message": str(exc)})
    except WebSocketDisconnect:
        return


@router.get("/eta/{stop_id}")
def get_eta(stop_id: int, time_of_day: float = 8.0, traffic_factor: float = 1.0, route: str = "04L"):
    eta_details = predict_eta_details(stop_id=stop_id, time_of_day=time_of_day, traffic_factor=traffic_factor, route=route)
    return {
        "stop_id": stop_id,
        "route": route,
        "time_of_day": time_of_day,
        "traffic_factor": traffic_factor,
        "eta_minutes": eta_details["eta_minutes"],
        "source": eta_details["source"],
    }


@router.get("/demand")
def get_demand():
    return load_demand_forecast()


@router.get("/fleet")
def get_fleet():
    return {"summary": fleet_store.summary(), "vehicles": [model_to_dict(vehicle) for vehicle in fleet_store.fleet()]}


@router.get("/alerts")
def get_alerts(include_acknowledged: bool = False):
    return {"alerts": [model_to_dict(alert) for alert in fleet_store.alerts(include_acknowledged=include_acknowledged)]}


@router.post("/alerts/{alert_id}/ack")
def acknowledge_alert(alert_id: str):
    alert = fleet_store.acknowledge_alert(alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="alert not found")
    return alert


@router.get("/incidents")
def get_incidents(limit: int = 50):
    return {"incidents": fleet_store.incidents(limit=limit)}


@router.get("/database/status")
def get_database_status():
    return fleet_store.database_status()


@router.get("/routes")
def get_routes(route: Optional[str] = None, q: Optional[str] = None):
    routes = list_routes()
    query = (route or q or "").strip().lower()
    if query:
        routes = [
            item for item in routes
            if query in item["route"].lower() or query in item["name"].lower()
        ]
    return {"routes": routes}


class RoutePayload(BaseModel):
    route: str
    name: str
    polyline: list[list[float]]

    @validator("route", "name")
    def required_text(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError("route and name are required")
        return value

    @validator("polyline")
    def valid_polyline(cls, value: list[list[float]]):
        validate_polyline(value)
        return value


@router.post("/routes")
def post_route(payload: RoutePayload, replace: bool = Query(False)):
    try:
        if sqlite_store.route_exists(payload.route) and not replace:
            raise HTTPException(status_code=409, detail=f"route id '{payload.route}' already exists")
        if sqlite_store.route_name_exists(payload.name, exclude_route=payload.route if replace else None):
            raise HTTPException(status_code=409, detail=f"route name '{payload.name}' already exists")
        sqlite_store.save_route(payload.route, payload.name, [(lat, lon) for lat, lon in payload.polyline])
        return {"status": "ok", "route": payload.route}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/routes/import")
async def import_routes(
    file: UploadFile = File(...),
    commit: bool = Form(False),
    replace: bool = Form(False),
    simplify_tolerance: float = Form(0.0),
):
    content = await file.read()
    try:
        routes = parse_route_file(file.filename or "", content)
        if simplify_tolerance > 0:
            routes = [
                route | {"polyline": simplify_polyline(route["polyline"], simplify_tolerance)}
                for route in routes
            ]
        errors = validate_imported_routes(routes, replace=replace)
        if errors:
            return {"status": "invalid", "filename": file.filename, "commit": False, "routes": routes, "errors": errors}
        if commit:
            for route in routes:
                sqlite_store.save_route(route["route"], route["name"], [(lat, lon) for lat, lon in route["polyline"]])
        return {
            "status": "committed" if commit else "preview",
            "filename": file.filename,
            "commit": commit,
            "count": len(routes),
            "routes": routes,
            "errors": [],
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/routes/{route}")
def delete_route(route: str):
    try:
        # simple delete using sqlite
        sqlite_store.init_db()
        conn = sqlite_store._connect()
        with conn:
            conn.execute("DELETE FROM routes WHERE route = ?", (route,))
        return {"status": "deleted", "route": route}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class CreateAlert(BaseModel):
    vehicle_id: str
    route: str
    severity: str = "medium"
    message: str


@router.post("/alerts")
def create_alert(payload: CreateAlert):
    try:
        ts = datetime.now(timezone.utc).isoformat()
        alert = OperatorAlertModel(id=str(uuid4()), severity=payload.severity, vehicle_id=payload.vehicle_id, route=payload.route, message=payload.message, timestamp=ts, acknowledged=False)
        sqlite_store.save_alert(alert)
        try:
            fleet_store._alerts.append(alert)
        except Exception:
            pass
        return {"status": "ok", "alert": model_to_dict(alert)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


class OperatorFeedback(BaseModel):
    alert_id: str
    vehicle_id: str
    route: str
    action: str


@router.post("/operator-feedback")
def create_operator_feedback(payload: OperatorFeedback):
    try:
        sqlite_store.save_operator_feedback(
            alert_id=payload.alert_id,
            vehicle_id=payload.vehicle_id,
            route=payload.route,
            action=payload.action,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/config")
def get_project_config():
    config = get_config().copy()
    return {
        "project": config.get("project", {}),
        "server": config.get("server", {}),
        "occupancy": config.get("occupancy", {}),
        "route_monitoring": config.get("route_monitoring", {}),
        "routes": config.get("routes", {}),
        "mock_telemetry": config.get("mock_telemetry", {}),
        "edge_counter": config.get("edge_counter", {}),
    }


@router.post("/chatbot")
def chatbot(query: ChatQuery):
    return fleet_store.recommendation(route=query.route, query=query.query)


def validate_polyline(polyline: list[list[float]]) -> None:
    if len(polyline) < 2:
        raise ValueError("polyline must contain at least two points")
    for index, point in enumerate(polyline):
        if len(point) != 2:
            raise ValueError(f"point {index} must be [latitude, longitude]")
        lat, lon = point
        if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in [lat, lon]):
            raise ValueError(f"point {index} contains non-numeric coordinates")
        if not -90 <= float(lat) <= 90 or not -180 <= float(lon) <= 180:
            raise ValueError(f"point {index} is outside latitude/longitude bounds")


def validate_imported_routes(routes: list[dict[str, Any]], replace: bool = False) -> list[str]:
    errors: list[str] = []
    seen_routes: set[str] = set()
    seen_names: set[str] = set()
    for index, route in enumerate(routes):
        route_id = str(route.get("route", "")).strip()
        name = str(route.get("name", "")).strip()
        if not route_id or not name:
            errors.append(f"route {index + 1}: route and name are required")
            continue
        if route_id.lower() in seen_routes:
            errors.append(f"route {route_id}: duplicate route id inside import")
        if name.lower() in seen_names:
            errors.append(f"route {route_id}: duplicate route name inside import")
        seen_routes.add(route_id.lower())
        seen_names.add(name.lower())
        try:
            validate_polyline(route.get("polyline", []))
        except ValueError as exc:
            errors.append(f"route {route_id}: {exc}")
        if sqlite_store.route_exists(route_id) and not replace:
            errors.append(f"route {route_id}: route id already exists")
        if sqlite_store.route_name_exists(name, exclude_route=route_id if replace else None):
            errors.append(f"route {route_id}: route name already exists")
    if not routes:
        errors.append("no routes found in uploaded file")
    return errors


def parse_route_file(filename: str, content: bytes) -> list[dict[str, Any]]:
    suffix = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if suffix in {"geojson", "json"}:
        return parse_geojson_routes(content)
    if suffix == "csv":
        return parse_csv_routes(content.decode("utf-8-sig"))
    if suffix == "zip":
        return parse_gtfs_routes(content)
    raise ValueError("supported route files: .geojson, .json, .csv, .zip GTFS")


def parse_geojson_routes(content: bytes) -> list[dict[str, Any]]:
    payload = json.loads(content.decode("utf-8-sig"))
    features = payload.get("features", []) if payload.get("type") == "FeatureCollection" else [payload]
    routes: list[dict[str, Any]] = []
    for index, feature in enumerate(features):
        geometry = feature.get("geometry", feature)
        props = feature.get("properties", {})
        route_id = str(props.get("route") or props.get("route_id") or props.get("id") or f"import-{index + 1}").strip()
        name = str(props.get("name") or props.get("route_name") or route_id).strip()
        coordinates = geometry.get("coordinates", [])
        if geometry.get("type") == "LineString":
            polyline = [[float(lat), float(lon)] for lon, lat, *_ in coordinates]
        elif geometry.get("type") == "MultiLineString":
            polyline = [[float(lat), float(lon)] for line in coordinates for lon, lat, *_ in line]
        else:
            continue
        routes.append({"route": route_id, "name": name, "polyline": polyline})
    return routes


def parse_csv_routes(text: str) -> list[dict[str, Any]]:
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        return []
    grouped: dict[str, dict[str, Any]] = {}
    for row in reader:
        route_id = (row.get("route") or row.get("route_id") or row.get("id") or "").strip()
        name = (row.get("name") or row.get("route_name") or route_id).strip()
        lat_value = row.get("latitude") or row.get("lat") or row.get("shape_pt_lat")
        lon_value = row.get("longitude") or row.get("lon") or row.get("lng") or row.get("shape_pt_lon")
        if not route_id or lat_value is None or lon_value is None:
            continue
        item = grouped.setdefault(route_id, {"route": route_id, "name": name, "polyline": []})
        item["polyline"].append([float(lat_value), float(lon_value)])
    return list(grouped.values())


def parse_gtfs_routes(content: bytes) -> list[dict[str, Any]]:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        names = set(archive.namelist())
        if "shapes.txt" not in names:
            raise ValueError("GTFS zip must include shapes.txt")
        route_names: dict[str, str] = {}
        if "routes.txt" in names:
            with archive.open("routes.txt") as handle:
                for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")):
                    route_id = row.get("route_id", "")
                    route_names[route_id] = row.get("route_short_name") or row.get("route_long_name") or route_id
        shape_to_route: dict[str, str] = {}
        if "trips.txt" in names:
            with archive.open("trips.txt") as handle:
                for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")):
                    if row.get("shape_id") and row.get("route_id"):
                        shape_to_route.setdefault(row["shape_id"], row["route_id"])
        shapes: dict[str, list[tuple[int, float, float]]] = {}
        with archive.open("shapes.txt") as handle:
            for row in csv.DictReader(io.TextIOWrapper(handle, encoding="utf-8-sig")):
                shape_id = row["shape_id"]
                sequence = int(float(row.get("shape_pt_sequence") or len(shapes.get(shape_id, []))))
                shapes.setdefault(shape_id, []).append((sequence, float(row["shape_pt_lat"]), float(row["shape_pt_lon"])))
    routes = []
    for shape_id, points in shapes.items():
        route_id = shape_to_route.get(shape_id, shape_id)
        points = sorted(points, key=lambda item: item[0])
        routes.append({
            "route": route_id,
            "name": route_names.get(route_id, route_id),
            "polyline": [[lat, lon] for _, lat, lon in points],
        })
    return routes


def simplify_polyline(points: list[list[float]], tolerance: float) -> list[list[float]]:
    if len(points) <= 2:
        return points

    def perpendicular_distance(point: list[float], start: list[float], end: list[float]) -> float:
        if start == end:
            return math.hypot(point[0] - start[0], point[1] - start[1])
        numerator = abs((end[1] - start[1]) * point[0] - (end[0] - start[0]) * point[1] + end[0] * start[1] - end[1] * start[0])
        denominator = math.hypot(end[1] - start[1], end[0] - start[0])
        return numerator / denominator

    max_distance = 0.0
    max_index = 0
    for index in range(1, len(points) - 1):
        distance = perpendicular_distance(points[index], points[0], points[-1])
        if distance > max_distance:
            max_index = index
            max_distance = distance
    if max_distance > tolerance:
        left = simplify_polyline(points[: max_index + 1], tolerance)
        right = simplify_polyline(points[max_index:], tolerance)
        return left[:-1] + right
    return [points[0], points[-1]]
