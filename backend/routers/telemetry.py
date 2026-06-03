import json
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from db import ROUTES, execute, rows
from routers.anomaly import check_anomalies

router = APIRouter(prefix="/api", tags=["telemetry"])
clients = []


class TelemetryPayload(BaseModel):
    vehicle_id: str
    timestamp: str
    passenger_count: int
    occupancy_tier: str
    lat: float
    lon: float
    speed_kph: float
    heading_deg: float
    route_id: str = "ayala-sm-carbon"


@router.post("/telemetry")
async def receive_telemetry(payload: TelemetryPayload):
    data = payload.model_dump() if hasattr(payload, "model_dump") else payload.dict()
    data["timestamp"] = data["timestamp"] or datetime.now(timezone.utc).isoformat()
    execute("""INSERT INTO telemetry (vehicle_id, route_id, timestamp, passenger_count, occupancy_tier, lat, lon, speed_kph, heading_deg)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""", (data["vehicle_id"], data["route_id"], data["timestamp"], data["passenger_count"], data["occupancy_tier"], data["lat"], data["lon"], data["speed_kph"], data["heading_deg"]))
    route = next((route for route in ROUTES if route["id"] == data["route_id"]), ROUTES[0])
    check_anomalies(data, route)
    for ws in list(clients):
        try:
            await ws.send_text(json.dumps(data))
        except Exception:
            clients.remove(ws)
    return {"ok": True}


@router.get("/fleet")
def get_fleet():
    return rows("""SELECT t.*, r.name AS route_name FROM telemetry t
                   JOIN (SELECT vehicle_id, MAX(id) AS max_id FROM telemetry GROUP BY vehicle_id) latest ON latest.max_id = t.id
                   LEFT JOIN routes r ON r.id = t.route_id ORDER BY t.vehicle_id""")


@router.get("/routes")
def get_routes():
    return rows("SELECT id, name FROM routes ORDER BY name")


@router.get("/stops")
def get_stops():
    return rows("SELECT * FROM stops ORDER BY route_id, name")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)
