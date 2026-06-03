from fastapi import APIRouter
from pydantic import BaseModel

from db import row, rows
from models.eta_model import haversine_m, predict_eta

router = APIRouter(prefix="/api", tags=["chatbot"])


class ChatRequest(BaseModel):
    message: str
    stop_id: str


def _nearest(stop_id):
    stop = row("SELECT * FROM stops WHERE id = ?", (stop_id,))
    latest = {}
    for item in rows("SELECT * FROM telemetry ORDER BY id DESC"):
        latest.setdefault(item["vehicle_id"], item)
    if not stop or not latest:
        return None
    ranked = []
    for vehicle in latest.values():
        distance = haversine_m(vehicle["lat"], vehicle["lon"], stop["lat"], stop["lon"])
        ranked.append((predict_eta(distance, vehicle["speed_kph"], vehicle["passenger_count"])["eta_seconds"], vehicle, stop))
    return sorted(ranked, key=lambda item: item[0])[0]


def _local_reply(context):
    if not context:
        return "I do not see live jeepney telemetry yet. Start the edge simulator, then I can recommend the best incoming ride."
    eta_seconds, vehicle, stop = context
    mins = max(1, round(eta_seconds / 60))
    tier = vehicle["occupancy_tier"]
    if tier == "GREEN":
        return f"Yes, board {vehicle['vehicle_id']} if it matches your route: it is available and about {mins} minutes from {stop['name']}. It has only {vehicle['passenger_count']} passengers, so it should be a comfortable ride."
    if tier == "YELLOW":
        return f"{vehicle['vehicle_id']} is okay to board if you are in a hurry: it is filling up and about {mins} minutes from {stop['name']}. If you prefer a less crowded ride, wait for a green jeepney."
    if tier == "RED":
        return f"I would wait if you can, because {vehicle['vehicle_id']} is already near capacity and about {mins} minutes from {stop['name']}. Board only if your trip is urgent."
    return f"Do not board {vehicle['vehicle_id']} right now: it is blinking red and may be overloaded. Please wait for the next safer jeepney."


@router.post("/chat")
def chat(request: ChatRequest):
    return {"reply": _local_reply(_nearest(request.stop_id))}
