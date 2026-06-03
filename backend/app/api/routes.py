import json
from typing import Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.core.config import default_route, get_config
from backend.app.core.compat import model_to_dict, validate_model
from backend.app.core.phase2 import load_demand_forecast, predict_eta_details
from backend.app.core.routes import list_routes
from backend.app.db import sqlite_store
from backend.app.core.state import fleet_store

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
def get_routes():
    # prefer database-backed routes when available
    try:
        db_routes = sqlite_store.load_routes()
        if db_routes:
            return {"routes": db_routes}
    except Exception:
        pass
    return {"routes": list_routes()}


class RoutePayload(BaseModel):
    route: str
    name: str
    polyline: list[list[float]]


@router.post("/routes")
def post_route(payload: RoutePayload):
    try:
        # save to DB
        sqlite_store.save_route(payload.route, payload.name, [(lat, lon) for lat, lon in payload.polyline])
        return {"status": "ok", "route": payload.route}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


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
