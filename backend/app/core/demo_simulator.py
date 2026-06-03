from __future__ import annotations

import math
import random
import threading
import time
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from backend.app.db import sqlite_store


class SyntheticFleetSimulator:
    def __init__(self, fleet_store: Any, vehicles_per_route: int = 3, interval_seconds: float = 2.0) -> None:
        self.fleet_store = fleet_store
        self.vehicles_per_route = vehicles_per_route
        self.interval_seconds = interval_seconds
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, name="loadsense-synthetic-fleet", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def _run(self) -> None:
        random.seed(2026)
        tick = 0
        while not self._stop.is_set():
            routes = [route for route in sqlite_store.load_routes() if len(route.get("polyline", [])) >= 2]
            for route_index, route in enumerate(routes):
                points = route["polyline"]
                for vehicle_index in range(self.vehicles_per_route):
                    position = ((tick * (0.006 + vehicle_index * 0.0015)) + vehicle_index / self.vehicles_per_route + route_index * 0.017) % 1.0
                    lat, lon = _point_at(points, position)
                    occupancy = _occupancy_for(tick, route_index, vehicle_index)
                    payload = SimpleNamespace(
                        vehicle_id=f"{route['route']}-{vehicle_index + 1:02d}",
                        route=route["route"],
                        latitude=lat,
                        longitude=lon,
                        occupancy=occupancy,
                        timestamp=datetime.now(UTC).isoformat(),
                        speed_kph=18 + ((tick + vehicle_index * 7 + route_index) % 19),
                        heading=None,
                        signal_quality="ok",
                    )
                    self.fleet_store.upsert_telemetry(payload)
            tick += 1
            self._stop.wait(self.interval_seconds)


def _point_at(points: list[dict[str, float]], ratio: float) -> tuple[float, float]:
    if len(points) == 1:
        return float(points[0]["latitude"]), float(points[0]["longitude"])
    scaled = ratio * (len(points) - 1)
    left = int(math.floor(scaled))
    right = min(len(points) - 1, left + 1)
    blend = scaled - left
    a = points[left]
    b = points[right]
    lat = float(a["latitude"]) + (float(b["latitude"]) - float(a["latitude"])) * blend
    lon = float(a["longitude"]) + (float(b["longitude"]) - float(a["longitude"])) * blend
    return lat, lon


def _occupancy_for(tick: int, route_index: int, vehicle_index: int) -> int:
    wave = math.sin((tick + route_index * 3 + vehicle_index * 5) / 7)
    base = 8 + round(wave * 5)
    if (tick + route_index + vehicle_index) % 37 == 0:
        return 18
    return max(1, min(16, base + vehicle_index * 2))
