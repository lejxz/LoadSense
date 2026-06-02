from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.app.core.occupancy import DEFAULT_CAPACITY, get_occupancy_tier
from backend.app.core.route_deviation import detect_route_deviation
from backend.app.core.phase2 import load_demand_forecast, predict_eta_details

router = APIRouter()


class Telemetry(BaseModel):
    vehicle_id: str
    route: str = "04L"
    latitude: float
    longitude: float
    occupancy: int
    timestamp: str


@router.post("/telemetry")
def receive_telemetry(t: Telemetry):
    # placeholder: accept telemetry and return current tier
    occupancy = t.occupancy
    tier = get_occupancy_tier(occupancy, DEFAULT_CAPACITY)
    deviation = detect_route_deviation(t.latitude, t.longitude, t.route)

    return {
        "vehicle_id": t.vehicle_id,
        "route": t.route,
        "tier": tier,
        "occupancy": occupancy,
        "route_deviation": deviation,
    }


@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            text = await websocket.receive_text()
            # For now just echo back acknowledgement
            await websocket.send_text(f"received {len(text)} bytes")
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
