import json
import pickle
from typing import Any, Dict, List

import pandas as pd

from backend.app.core.config import config_value, repo_path

ETA_MODEL_PATH = repo_path(config_value("artifacts", "eta_model", default="cloud/artifacts/eta_model.pkl"))
DEMAND_FORECAST_PATH = repo_path(config_value("artifacts", "demand_forecast", default="cloud/artifacts/demand_forecast.json"))


def load_eta_model() -> Any:
    if ETA_MODEL_PATH.exists():
        with ETA_MODEL_PATH.open("rb") as handle:
            return pickle.load(handle)
    return None


def predict_eta(stop_id: int, time_of_day: float = 8.0, traffic_factor: float = 1.0, route: str = "04L") -> float:
    return predict_eta_details(stop_id=stop_id, time_of_day=time_of_day, traffic_factor=traffic_factor, route=route)["eta_minutes"]


def predict_eta_details(stop_id: int, time_of_day: float = 8.0, traffic_factor: float = 1.0, route: str = "04L") -> Dict[str, Any]:
    model = load_eta_model()
    if model is None:
        eta_minutes = round(
            float(config_value("eta_fallback", "base_minutes", default=5.0))
            + stop_id * float(config_value("eta_fallback", "stop_weight", default=0.75))
            + traffic_factor * float(config_value("eta_fallback", "traffic_weight", default=1.5))
            + time_of_day * float(config_value("eta_fallback", "time_of_day_weight", default=0.05)),
            2,
        )
        return {"eta_minutes": eta_minutes, "source": "fallback"}

    frame = pd.DataFrame(
        [{
            "stop_index": stop_id,
            "time_of_day": time_of_day,
            "traffic_factor": traffic_factor,
            "route": route,
        }]
    )
    prediction = model.predict(frame)[0]
    return {"eta_minutes": round(float(prediction), 2), "source": "model"}


def load_demand_forecast() -> Dict[str, List[Dict[str, Any]]]:
    if DEMAND_FORECAST_PATH.exists():
        with DEMAND_FORECAST_PATH.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    return {"forecast": []}
