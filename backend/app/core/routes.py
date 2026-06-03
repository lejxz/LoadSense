from typing import List

from backend.app.core.config import default_route, route_names
from backend.app.core.route_deviation import ROUTE_POLYLINES
from backend.app.db import sqlite_store


ROUTE_NAMES = route_names()


def get_route_stops(route: str) -> List[dict]:
    points = sqlite_store.load_route_polyline(route) or ROUTE_POLYLINES.get(route) or ROUTE_POLYLINES.get(default_route()) or [(10.3157, 123.8854), (10.3308, 123.8990)]
    if len(points) > 8:
        indexes = sorted({0, len(points) - 1, *[round((len(points) - 1) * ratio) for ratio in (0.2, 0.35, 0.5, 0.65, 0.8)]})
        points = [points[index] for index in indexes]
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
    db_routes = sqlite_store.load_routes()
    if db_routes:
        return db_routes
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
