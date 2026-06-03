"""
Fetch public OpenStreetMap Cebu corridor geometry from Overpass and store it in
the local SQLite route table. OSM has sparse formal jeepney route relations in
Cebu, so this imports route relations when available and otherwise uses named
Cebu road corridors that PUV routes actually run on.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.db import sqlite_store

OVERPASS_CANDIDATES = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

CEBU_BBOX = "10.245,123.835,10.390,123.965"
TARGET_ROADS = [
    "Osmeña Boulevard",
    "General Maxilom Avenue",
    "N. Bacalso Avenue",
    "M. J. Cuenco Avenue",
    "Escario Street",
    "Gorordo Avenue",
    "V. Rama Avenue",
    "Cebu South Road",
    "Colon Street",
    "A. S. Fortuna Street",
    "M. L. Quezon Avenue",
    "Ouano Avenue",
]


def post_overpass(query: str, timeout: int = 90) -> dict[str, Any]:
    last_exc: Exception | None = None
    for endpoint in OVERPASS_CANDIDATES:
        try:
            print(f"Trying Overpass endpoint: {endpoint}")
            response = requests.post(endpoint, data={"data": query}, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            print(f"Overpass endpoint failed: {endpoint} {exc}")
            last_exc = exc
            time.sleep(2)
    if last_exc:
        raise last_exc
    raise RuntimeError("no Overpass endpoint configured")


def route_relation_query(bbox: str) -> str:
    return f"""
    [out:json][timeout:60];
    (
      relation["route"~"bus|share_taxi|minibus|jeepney"]({bbox});
      relation["network"~"Cebu|PUJ|Jeepney|MyBus",i]({bbox});
    );
    out body;
    >;
    out skel qt;
    """


def named_road_query(bbox: str) -> str:
    names = "|".join(re.escape(name) for name in TARGET_ROADS)
    return f"""
    [out:json][timeout:60];
    (
      way["highway"~"primary|secondary|tertiary|trunk"]["name"~"{names}",i]({bbox});
    );
    out body;
    >;
    out skel qt;
    """


def elements_to_maps(data: dict[str, Any]) -> tuple[dict[int, tuple[float, float]], dict[int, dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[int, tuple[float, float]] = {}
    ways: dict[int, dict[str, Any]] = {}
    relations: list[dict[str, Any]] = []
    for element in data.get("elements", []):
        if element.get("type") == "node":
            nodes[element["id"]] = (float(element["lat"]), float(element["lon"]))
        elif element.get("type") == "way":
            ways[element["id"]] = element
        elif element.get("type") == "relation":
            relations.append(element)
    return nodes, ways, relations


def dedupe_points(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    seen: set[tuple[float, float]] = set()
    for lat, lon in points:
        key = (round(lat, 7), round(lon, 7))
        if key in seen:
            continue
        seen.add(key)
        result.append((lat, lon))
    return result


def slug(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
    return text[:32] or "CEBU-ROUTE"


def assemble_relation_routes(data: dict[str, Any]) -> list[dict[str, Any]]:
    nodes, ways, relations = elements_to_maps(data)
    routes: list[dict[str, Any]] = []
    for relation in relations:
        tags = relation.get("tags", {})
        points: list[tuple[float, float]] = []
        for member in relation.get("members", []):
            if member.get("type") != "way" or member.get("ref") not in ways:
                continue
            way = ways[member["ref"]]
            points.extend(nodes[node_id] for node_id in way.get("nodes", []) if node_id in nodes)
        points = dedupe_points(points)
        if len(points) < 2:
            continue
        name = tags.get("name") or tags.get("ref") or f"OSM relation {relation['id']}"
        route_id = tags.get("ref") or slug(name)
        routes.append({"route": str(route_id), "name": name, "polyline": points})
    return routes


def assemble_road_routes(data: dict[str, Any]) -> list[dict[str, Any]]:
    nodes, ways, _ = elements_to_maps(data)
    grouped: dict[str, list[tuple[int, list[tuple[float, float]]]]] = {}
    for way_id, way in ways.items():
        name = way.get("tags", {}).get("name")
        if not name:
            continue
        points = [nodes[node_id] for node_id in way.get("nodes", []) if node_id in nodes]
        if len(points) >= 2:
            grouped.setdefault(name, []).append((way_id, points))

    routes: list[dict[str, Any]] = []
    for name in TARGET_ROADS:
        segments = grouped.get(name)
        if not segments:
            continue
        points: list[tuple[float, float]] = []
        for _, segment in sorted(segments, key=lambda item: item[0]):
            points.extend(segment)
        points = dedupe_points(points)
        if len(points) >= 2:
            routes.append({"route": f"CEBU-{slug(name)}", "name": name, "polyline": points[:220]})
    return routes


def save_routes(routes: list[dict[str, Any]], replace: bool) -> None:
    sqlite_store.init_db()
    if replace:
        with sqlite_store._connect() as conn:
            conn.execute("DELETE FROM routes")
    for route in routes:
        sqlite_store.save_route(route["route"], route["name"], route["polyline"])


def write_geojson(routes: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"route_id": route["route"], "route_name": route["name"], "source": "OpenStreetMap Overpass"},
                "geometry": {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in route["polyline"]]},
            }
            for route in routes
        ],
    }
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bbox", default=CEBU_BBOX, help="minlat,minlon,maxlat,maxlon")
    parser.add_argument("--replace", action="store_true", help="Replace the local routes table")
    parser.add_argument("--output", default="data/cebu_osm_routes.geojson")
    args = parser.parse_args()

    relation_data = post_overpass(route_relation_query(args.bbox))
    routes = assemble_relation_routes(relation_data)
    print(f"OSM public transport relations with geometry: {len(routes)}")

    if len(routes) < 3:
        road_data = post_overpass(named_road_query(args.bbox))
        routes = assemble_road_routes(road_data)
        print(f"Using named Cebu road corridors from OSM: {len(routes)}")

    if not routes:
        raise SystemExit("No Cebu route geometry found from Overpass")

    write_geojson(routes, ROOT / args.output)
    save_routes(routes, replace=args.replace)
    print(f"Stored {len(routes)} routes in SQLite and wrote {args.output}")


if __name__ == "__main__":
    main()
