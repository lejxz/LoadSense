import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from prophet import Prophet

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import config_value


def build_forecast(frame: pd.DataFrame):
    frame = frame.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    now = datetime.now(UTC).replace(minute=0, second=0, microsecond=0)

    forecasts = []
    for route, route_frame in frame.groupby("route"):
        history = route_frame.resample("h", on="timestamp")["count"].mean().reset_index().rename(columns={"timestamp": "ds", "count": "y"})
        history["ds"] = pd.to_datetime(history["ds"], utc=True).dt.tz_convert(None)

        try:
            model = Prophet(daily_seasonality=True, weekly_seasonality=False, yearly_seasonality=False)
            model.fit(history)

            future = model.make_future_dataframe(periods=24, freq="h", include_history=False)
            forecast = model.predict(future)
            route_forecast = [
                {
                    "route": route,
                    "timestamp": row["ds"].replace(tzinfo=UTC).isoformat(),
                    "expected_load": round(max(0.0, float(row["yhat"])), 2),
                }
                for _, row in forecast[["ds", "yhat"]].iterrows()
            ]
        except Exception:
            mean_load = float(history["y"].mean()) if not history.empty else 0.0
            route_forecast = [
                {
                    "route": route,
                    "timestamp": (now + pd.Timedelta(hours=offset)).isoformat(),
                    "expected_load": round(mean_load, 2),
                }
                for offset in range(24)
            ]

        forecasts.extend(route_forecast)

    return {"generated_at": now.isoformat(), "forecast": forecasts, "model": "prophet"}


def main():
    parser = argparse.ArgumentParser(description="Generate a lightweight demand forecast JSON from synthetic logs")
    parser.add_argument("--input", default=config_value("data", "synthetic_history", default=os.path.join("data", "synthetic_occupancy_logs.csv")))
    parser.add_argument("--output", default=config_value("artifacts", "demand_forecast", default=os.path.join("cloud", "artifacts", "demand_forecast.json")))
    args = parser.parse_args()

    frame = pd.read_csv(args.input)
    forecast = build_forecast(frame)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(forecast, handle, indent=2)

    print(f"saved demand forecast to {args.output}")
    print(f"forecast rows: {len(forecast['forecast'])}")


if __name__ == "__main__":
    main()
