from typing import List

from backend.app.core.config import default_route, route_names
from backend.app.core.route_deviation import ROUTE_POLYLINES
from backend.app.db import sqlite_store


ROUTE_NAMES = route_names()


def get_route_stops(route: str) -> List[dict]:
    points = ROUTE_POLYLINES.get(route) or sqlite_store.load_route_polyline(route) or ROUTE_POLYLINES[default_route()]
    return [
        {
            "stop_id": index,
            "name": f"{ROUTE_NAMES.get(route, route)} Stop {index + 1}",
            "latitude": point[0],
            "longitude": point[1],
        }
        for index, point in enumerate(points)
    ]


def list_routes() -> List[dict]:
    return [
        {
            "route": route,
            "name": ROUTE_NAMES.get(route, route),
            "stops": get_route_stops(route),
            "polyline": [{"latitude": lat, "longitude": lon} for lat, lon in points],
        }
        for route, points in ROUTE_POLYLINES.items()
    ]


def nearest_stop_id(route: str, latitude: float, longitude: float) -> int:
    stops = get_route_stops(route)
    best_index = 0
    best_score = float("inf")
    for stop in stops:
        score = abs(stop["latitude"] - latitude) + abs(stop["longitude"] - longitude)
        if score < best_score:
            best_index = stop["stop_id"]
            best_score = score
    return best_index
