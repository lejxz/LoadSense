from datetime import datetime, timezone

from fastapi import APIRouter

from db import execute, row, rows
from models.eta_model import haversine_m

router = APIRouter(prefix="/api", tags=["anomalies"])


def check_anomalies(payload, route):
    nearest = min(haversine_m(payload["lat"], payload["lon"], lat, lon) for lat, lon in route["waypoints"])
    if nearest > 200:
        execute("INSERT INTO anomalies (vehicle_id, anomaly_type, timestamp, status, details) VALUES (?, ?, ?, ?, ?)", (payload["vehicle_id"], "ROUTE_DEVIATION", payload["timestamp"], "pending_operator_review", f"{nearest:.0f}m from expected route"))
    if payload["occupancy_tier"] == "BLINKING_RED":
        execute("INSERT INTO anomalies (vehicle_id, anomaly_type, timestamp, status, details) VALUES (?, ?, ?, ?, ?)", (payload["vehicle_id"], "OVERLOAD", payload["timestamp"], "pending_operator_review", "Passenger count exceeds safe 16-seat threshold"))


def check_signal_loss():
    now = datetime.now(timezone.utc)
    for item in rows("SELECT vehicle_id, MAX(timestamp) AS timestamp FROM telemetry GROUP BY vehicle_id"):
        last = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
        if (now - last).total_seconds() > 10 and not row("SELECT id FROM anomalies WHERE vehicle_id = ? AND anomaly_type = 'SIGNAL_ANOMALY' AND status = 'pending_operator_review'", (item["vehicle_id"],)):
            execute("INSERT INTO anomalies (vehicle_id, anomaly_type, timestamp, status, details) VALUES (?, ?, ?, ?, ?)", (item["vehicle_id"], "SIGNAL_ANOMALY", now.isoformat(), "pending_operator_review", "No telemetry for more than 10 seconds"))


@router.get("/anomalies")
def get_anomalies():
    check_signal_loss()
    return rows("SELECT * FROM anomalies ORDER BY status = 'pending_operator_review' DESC, timestamp DESC LIMIT 100")


@router.patch("/anomalies/{anomaly_id}")
def acknowledge_anomaly(anomaly_id: int):
    execute("UPDATE anomalies SET status = 'notified_commuters' WHERE id = ?", (anomaly_id,))
    return {"ok": True, "id": anomaly_id, "status": "notified_commuters"}
