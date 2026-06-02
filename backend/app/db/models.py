# Placeholder DB models. Replace with SQLAlchemy or another ORM as needed.

from pydantic import BaseModel


class VehicleState(BaseModel):
    vehicle_id: str
    lat: float
    lon: float
    occupancy: int
    timestamp: str
