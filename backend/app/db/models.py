from typing import Any, Dict, Optional

from pydantic import BaseModel


class VehicleState(BaseModel):
    vehicle_id: str
    route: str
    latitude: float
    longitude: float
    occupancy: int
    capacity: int
    tier: str
    timestamp: str
    eta_minutes: float
    eta_source: str
    next_stop_id: int
    route_deviation: Dict[str, Any]
    signal_quality: str = "ok"
    speed_kph: Optional[float] = None
    heading: Optional[float] = None


class OperatorAlert(BaseModel):
    id: str
    severity: str
    vehicle_id: str
    route: str
    message: str
    timestamp: str
    acknowledged: bool = False
