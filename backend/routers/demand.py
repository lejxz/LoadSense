from fastapi import APIRouter

from db import row
from models.demand_model import forecast_demand

router = APIRouter(prefix="/api", tags=["demand"])


@router.get("/demand/{route_id}")
def get_demand(route_id: str):
    return {"route": row("SELECT id, name FROM routes WHERE id = ?", (route_id,)) or {"id": route_id, "name": route_id}, "forecast": forecast_demand(route_id)}
