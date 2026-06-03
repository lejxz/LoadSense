from fastapi import APIRouter, HTTPException

from db import row
from models.eta_model import haversine_m, predict_eta

router = APIRouter(prefix="/api", tags=["eta"])


@router.get("/eta/{vehicle_id}/{stop_id}")
def get_eta(vehicle_id: str, stop_id: str):
    vehicle = row("SELECT * FROM telemetry WHERE vehicle_id = ? ORDER BY id DESC LIMIT 1", (vehicle_id,))
    stop = row("SELECT * FROM stops WHERE id = ? LIMIT 1", (stop_id,))
    if not vehicle or not stop:
        raise HTTPException(status_code=404, detail="Vehicle or stop not found")
    distance = haversine_m(vehicle["lat"], vehicle["lon"], stop["lat"], stop["lon"])
    return {"vehicle_id": vehicle_id, "stop_id": stop_id, "distance_to_stop_m": round(distance), **predict_eta(distance, vehicle["speed_kph"], vehicle["passenger_count"])}
