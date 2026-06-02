import math
from typing import Dict, Iterable, Tuple


RoutePoint = Tuple[float, float]


ROUTE_POLYLINES: Dict[str, list[RoutePoint]] = {
    "04L": [(14.5992, 120.9840), (14.6001, 120.9850), (14.6009, 120.9862), (14.6017, 120.9870)],
    "08A": [(14.5988, 120.9835), (14.5996, 120.9846), (14.6004, 120.9854), (14.6011, 120.9864)],
    "12B": [(14.5990, 120.9844), (14.5999, 120.9855), (14.6007, 120.9866), (14.6014, 120.9875)],
    "17C": [(14.5986, 120.9838), (14.5994, 120.9849), (14.6002, 120.9858), (14.6010, 120.9868)],
}


def _project(lat: float, lon: float, origin_lat: float) -> tuple[float, float]:
    meters_per_degree_lat = 111_132.0
    meters_per_degree_lon = 111_320.0 * math.cos(math.radians(origin_lat))
    x = lon * meters_per_degree_lon
    y = lat * meters_per_degree_lat
    return x, y


def _distance_point_to_segment(point: RoutePoint, start: RoutePoint, end: RoutePoint) -> float:
    px, py = _project(point[0], point[1], point[0])
    sx, sy = _project(start[0], start[1], point[0])
    ex, ey = _project(end[0], end[1], point[0])
    dx = ex - sx
    dy = ey - sy
    if dx == 0 and dy == 0:
        return math.hypot(px - sx, py - sy)

    t = ((px - sx) * dx + (py - sy) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    nearest_x = sx + t * dx
    nearest_y = sy + t * dy
    return math.hypot(px - nearest_x, py - nearest_y)


def distance_to_route_meters(latitude: float, longitude: float, route: str) -> float:
    points = ROUTE_POLYLINES.get(route)
    if not points:
        raise KeyError(f"unknown route '{route}'")

    probe = (latitude, longitude)
    distances = [
        _distance_point_to_segment(probe, start, end)
        for start, end in zip(points, points[1:])
    ]
    return min(distances)


def detect_route_deviation(latitude: float, longitude: float, route: str, threshold_meters: float = 200.0) -> dict:
    deviation_meters = round(distance_to_route_meters(latitude, longitude, route), 2)
    return {
        "route": route,
        "deviation_meters": deviation_meters,
        "threshold_meters": threshold_meters,
        "anomaly": deviation_meters > threshold_meters,
    }
