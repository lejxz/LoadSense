from __future__ import annotations

import math
import re
from typing import Any, Iterable, Optional


WALKING_RADIUS_METERS = 500.0
RELAXED_RADIUS_METERS = 1500.0
DEFAULT_SPEED_KPH = 30.0


def _stop(name: str, latitude: float, longitude: float) -> dict[str, Any]:
    return {"name": name, "latitude": latitude, "longitude": longitude}


SYNTHETIC_REGIONAL_ROUTES: list[dict[str, Any]] = [
    {
        "route": "MNL-EDSA",
        "name": "Metro Manila EDSA Carousel: Monumento - PITX",
        "city": "Metro Manila",
        "zone": "EDSA",
        "type": "Bus",
        "stops": [
            _stop("Monumento", 14.6571, 120.9848),
            _stop("Balintawak", 14.6577, 121.0034),
            _stop("North Avenue", 14.6537, 121.0323),
            _stop("Quezon Avenue", 14.6416, 121.0388),
            _stop("Ortigas Center", 14.5869, 121.0564),
            _stop("Guadalupe", 14.5662, 121.0457),
            _stop("Ayala MRT", 14.5495, 121.0266),
            _stop("SM Mall of Asia", 14.5353, 120.9822),
            _stop("PITX", 14.5094, 120.9912),
        ],
    },
    {
        "route": "MNL-QA",
        "name": "Metro Manila Quezon Avenue: Fairview - Quiapo",
        "city": "Metro Manila",
        "zone": "Commonwealth / Quezon Avenue",
        "type": "Modern Jeepney",
        "stops": [
            _stop("Fairview Center Mall", 14.7367, 121.0624),
            _stop("Regalado Avenue", 14.7136, 121.0616),
            _stop("Commonwealth Market", 14.6817, 121.0836),
            _stop("Philcoa", 14.6558, 121.0523),
            _stop("Quezon Memorial Circle", 14.6510, 121.0490),
            _stop("Welcome Rotonda", 14.6184, 121.0012),
            _stop("UST Espana", 14.6099, 120.9896),
            _stop("Quiapo Church", 14.5989, 120.9830),
        ],
    },
    {
        "route": "MNL-TAFT",
        "name": "Metro Manila Taft Avenue: Lawton - Baclaran - PITX",
        "city": "Metro Manila",
        "zone": "Taft / Pasay",
        "type": "Jeepney",
        "stops": [
            _stop("Lawton", 14.5947, 120.9791),
            _stop("UN Avenue", 14.5825, 120.9844),
            _stop("Pedro Gil", 14.5742, 120.9868),
            _stop("Vito Cruz", 14.5637, 120.9940),
            _stop("EDSA Taft", 14.5376, 121.0008),
            _stop("Baclaran Church", 14.5312, 120.9945),
            _stop("SM Mall of Asia", 14.5353, 120.9822),
            _stop("PITX", 14.5094, 120.9912),
        ],
    },
    {
        "route": "DVO-01",
        "name": "Davao City Roxas - Ateneo - SM Ecoland",
        "city": "Davao City",
        "zone": "Poblacion / Ecoland",
        "type": "Jeepney",
        "stops": [
            _stop("Roxas Night Market", 7.0716, 125.6136),
            _stop("Ateneo de Davao", 7.0704, 125.6122),
            _stop("People's Park", 7.0649, 125.6084),
            _stop("Davao City Hall", 7.0644, 125.6070),
            _stop("Bankerohan Market", 7.0611, 125.6023),
            _stop("Matina Crossing", 7.0434, 125.5907),
            _stop("SM City Davao", 7.0497, 125.5884),
            _stop("Ecoland Terminal", 7.0531, 125.5918),
        ],
    },
    {
        "route": "DVO-02",
        "name": "Davao City Buhangin - Abreeza - Bankerohan",
        "city": "Davao City",
        "zone": "Buhangin / Bajada",
        "type": "Modern Jeepney",
        "stops": [
            _stop("Buhangin Public Market", 7.1123, 125.6150),
            _stop("Davao International Airport", 7.1255, 125.6468),
            _stop("Sasa Wharf", 7.1117, 125.6620),
            _stop("SM Lanang Premier", 7.0993, 125.6307),
            _stop("Abreeza Mall", 7.0910, 125.6110),
            _stop("Victoria Plaza", 7.0828, 125.6101),
            _stop("Roxas Avenue", 7.0716, 125.6136),
            _stop("Bankerohan Market", 7.0611, 125.6023),
        ],
    },
    {
        "route": "DVO-03",
        "name": "Davao City Toril - Matina - City Hall",
        "city": "Davao City",
        "zone": "Toril / Matina",
        "type": "Bus",
        "stops": [
            _stop("Toril Proper", 7.0178, 125.4997),
            _stop("Davao Baywalk", 7.0242, 125.5232),
            _stop("Ulas Crossing", 7.0327, 125.5457),
            _stop("Matina Aplaya", 7.0409, 125.5723),
            _stop("Matina Crossing", 7.0434, 125.5907),
            _stop("SM City Davao", 7.0497, 125.5884),
            _stop("Bankerohan Market", 7.0611, 125.6023),
            _stop("Davao City Hall", 7.0644, 125.6070),
        ],
    },
    {
        "route": "ILO-01",
        "name": "Iloilo City SM City - City Proper - Fort San Pedro",
        "city": "Iloilo City",
        "zone": "Mandurriao / City Proper",
        "type": "Modern Jeepney",
        "stops": [
            _stop("SM City Iloilo", 10.7144, 122.5527),
            _stop("Plazuela de Iloilo", 10.7149, 122.5504),
            _stop("Iloilo Esplanade", 10.7041, 122.5518),
            _stop("Molo Plaza", 10.6968, 122.5451),
            _stop("University of San Agustin", 10.7003, 122.5642),
            _stop("Iloilo City Hall", 10.6929, 122.5736),
            _stop("Calle Real", 10.6941, 122.5685),
            _stop("Fort San Pedro", 10.6920, 122.5810),
        ],
    },
    {
        "route": "ILO-02",
        "name": "Iloilo City Jaro - CPU - Smallville - Atria",
        "city": "Iloilo City",
        "zone": "Jaro / Mandurriao",
        "type": "Jeepney",
        "stops": [
            _stop("Jaro Plaza", 10.7245, 122.5599),
            _stop("Jaro Cathedral", 10.7240, 122.5592),
            _stop("Central Philippine University", 10.7290, 122.5489),
            _stop("Tagbak Terminal", 10.7511, 122.5685),
            _stop("Megaworld Iloilo", 10.7167, 122.5464),
            _stop("Smallville Complex", 10.7146, 122.5483),
            _stop("Atria Park District", 10.7061, 122.5475),
            _stop("Iloilo Esplanade", 10.7041, 122.5518),
        ],
    },
    {
        "route": "ILO-03",
        "name": "Iloilo City Mohon - Molo - Festive Walk",
        "city": "Iloilo City",
        "zone": "Molo / Mandurriao",
        "type": "E-Jeep",
        "stops": [
            _stop("Mohon Terminal", 10.6796, 122.5317),
            _stop("Oton Road", 10.6871, 122.5367),
            _stop("Molo Church", 10.6965, 122.5455),
            _stop("Molo Plaza", 10.6968, 122.5451),
            _stop("Iloilo Esplanade", 10.7041, 122.5518),
            _stop("Atria Park District", 10.7061, 122.5475),
            _stop("SM City Iloilo", 10.7144, 122.5527),
            _stop("Festive Walk Iloilo", 10.7177, 122.5452),
        ],
    },
]


LANDMARKS: list[dict[str, Any]] = [
    {"name": "Ayala Center Cebu", "city": "Cebu City", "latitude": 10.3173, "longitude": 123.9058, "aliases": ["ayala", "ayala center"]},
    {"name": "SM City Cebu", "city": "Cebu City", "latitude": 10.3115, "longitude": 123.9183, "aliases": ["sm cebu", "sm city"]},
    {"name": "Colon Street", "city": "Cebu City", "latitude": 10.2964, "longitude": 123.8997, "aliases": ["colon"]},
    {"name": "Carbon Market", "city": "Cebu City", "latitude": 10.2927, "longitude": 123.9006, "aliases": ["carbon", "carbon market"]},
    {"name": "Fuente Osmena Circle", "city": "Cebu City", "latitude": 10.3093, "longitude": 123.8930, "aliases": ["fuente", "fuente osmena"]},
    {"name": "Cebu IT Park", "city": "Cebu City", "latitude": 10.3306, "longitude": 123.9067, "aliases": ["it park", "cebu it park"]},
    {"name": "Parkmall Mandaue", "city": "Mandaue", "latitude": 10.3337, "longitude": 123.9336, "aliases": ["parkmall"]},
    {"name": "SM Seaside City Cebu", "city": "Cebu City", "latitude": 10.2810, "longitude": 123.8817, "aliases": ["sm seaside", "seaside"]},
]


ROUTE_METADATA: dict[str, dict[str, Any]] = {
    route["route"]: {
        "city": route["city"],
        "zone": route["zone"],
        "type": route["type"],
        "stops": [
            {"stop_id": index, **stop}
            for index, stop in enumerate(route["stops"])
        ],
        "landmarks": [stop["name"] for stop in route["stops"]],
        "endpoints": [route["stops"][0]["name"], route["stops"][-1]["name"]],
    }
    for route in SYNTHETIC_REGIONAL_ROUTES
}


LANGUAGE_KEYWORDS = {
    "ceb": ["asa", "paingon", "padung", "gikan", "unsa", "sakay", "dyip", "diri"],
    "tl": ["saan", "papunta", "pumunta", "daan", "byahe", "sakay", "dito", "dyip"],
    "ilo": ["diin", "pakadto", "sakyan", "jeep"],
    "ilocano": ["sadino", "mapan", "lugan"],
}


DESTINATION_PATTERNS = [
    r"(?:how do i get to|how to get to|which .*? to|what .*? goes to|route to|going to|go to|reach|towards?|to)\s+(.+)",
    r"(?:saan .*? papunta sa|paano pumunta sa|papunta sa|papuntang|punta sa|daan sa|byahe sa)\s+(.+)",
    r"(?:asa .*? paingon sa|unsa .*? paingon sa|paingon sa|padung sa|punta sa)\s+(.+)",
    r"(?:diin .*? pakadto sa|pakadto sa)\s+(.+)",
    r"(?:sadino .*? mapan iti|mapan iti)\s+(.+)",
]


def route_metadata(route_id: str) -> dict[str, Any]:
    return ROUTE_METADATA.get(route_id, {})


def haversine_meters(a_lat: float, a_lon: float, b_lat: float, b_lon: float) -> float:
    radius = 6_371_000.0
    d_lat = math.radians(b_lat - a_lat)
    d_lon = math.radians(b_lon - a_lon)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(a_lat))
        * math.cos(math.radians(b_lat))
        * math.sin(d_lon / 2) ** 2
    )
    return radius * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_eta_minutes(distance_meters: float, speed_kph: Optional[float]) -> float:
    speed = max(5.0, float(speed_kph or DEFAULT_SPEED_KPH))
    return round((distance_meters / 1000.0) / speed * 60.0, 1)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9\s]", " ", value.lower())).strip()


def detect_language(query: str) -> str:
    normalized = f" {normalize_text(query)} "
    scores = {
        language: sum(1 for word in words if f" {word} " in normalized)
        for language, words in LANGUAGE_KEYWORDS.items()
    }
    language, score = max(scores.items(), key=lambda item: item[1])
    return language if score else "en"


def infer_city(points: Iterable[dict[str, Any]], route_name: str = "") -> str:
    name = route_name.lower()
    if "davao" in name:
        return "Davao City"
    if "iloilo" in name:
        return "Iloilo City"
    if "metro manila" in name or "manila" in name:
        return "Metro Manila"
    latitudes = [float(point["latitude"]) for point in points if _valid_coord(point)]
    longitudes = [float(point["longitude"]) for point in points if _valid_coord(point)]
    if not latitudes or not longitudes:
        return "Unknown"
    lat = sum(latitudes) / len(latitudes)
    lon = sum(longitudes) / len(longitudes)
    if 14.3 <= lat <= 14.9 and 120.8 <= lon <= 121.2:
        return "Metro Manila"
    if 6.9 <= lat <= 7.2 and 125.4 <= lon <= 125.8:
        return "Davao City"
    if 10.6 <= lat <= 10.8 and 122.45 <= lon <= 122.65:
        return "Iloilo City"
    if 10.15 <= lat <= 10.55 and 123.65 <= lon <= 124.10:
        return "Cebu"
    return "Philippines"


def build_place_index(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    places: list[dict[str, Any]] = []
    for landmark in LANDMARKS:
        places.append({
            "name": landmark["name"],
            "city": landmark["city"],
            "latitude": landmark["latitude"],
            "longitude": landmark["longitude"],
            "aliases": landmark.get("aliases", []),
            "kind": "landmark",
        })
    for route in routes:
        city = route.get("city") or infer_city(route.get("polyline", []), route.get("name", ""))
        for stop in route_points(route, prefer_stops=True):
            places.append({
                "name": stop["name"],
                "city": city,
                "route": route.get("route"),
                "latitude": stop["latitude"],
                "longitude": stop["longitude"],
                "aliases": [stop["name"], route.get("name", ""), route.get("route", "")],
                "kind": "stop",
            })
    return _dedupe_places(places)


def search_places(routes: list[dict[str, Any]], query: str = "", limit: int = 12) -> list[dict[str, Any]]:
    places = build_place_index(routes)
    needle = normalize_text(query or "")
    if not needle:
        return places[:limit]
    scored: list[tuple[int, dict[str, Any]]] = []
    for place in places:
        haystack = " ".join([place["name"], place.get("city", ""), *(place.get("aliases") or [])])
        normalized = normalize_text(haystack)
        if needle in normalized:
            scored.append((100 + len(needle), place))
        elif all(token in normalized for token in needle.split()):
            scored.append((70 + len(needle), place))
    scored.sort(key=lambda item: (-item[0], item[1]["name"]))
    return [item[1] for item in scored[:limit]]


def extract_destination(query: str, routes: list[dict[str, Any]], explicit_destination: str = "") -> str:
    if explicit_destination.strip():
        return explicit_destination.strip()
    normalized = normalize_text(query)
    places = build_place_index(routes)
    matched_place = _best_place_text_match(normalized, places)
    if matched_place:
        return matched_place["name"]
    for pattern in DESTINATION_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return _clean_destination(match.group(1))
    return ""


def resolve_place(
    text: str,
    routes: list[dict[str, Any]],
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    default_name: str = "Current location",
) -> Optional[dict[str, Any]]:
    if latitude is not None and longitude is not None:
        return {"name": text.strip() or default_name, "latitude": float(latitude), "longitude": float(longitude), "kind": "coordinate"}
    raw = (text or "").strip()
    normalized = normalize_text(raw)
    if not raw:
        return None
    coord_match = re.search(r"(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)", raw)
    if coord_match:
        return {
            "name": raw,
            "latitude": float(coord_match.group(1)),
            "longitude": float(coord_match.group(2)),
            "kind": "coordinate",
        }
    if normalized in {"current location", "my location", "here", "dito", "diri"}:
        return None
    places = build_place_index(routes)
    matched = _best_place_text_match(normalized, places)
    if matched:
        return matched
    return None


def find_transit_suggestions(
    routes: list[dict[str, Any]],
    vehicles: list[dict[str, Any]],
    query: str = "",
    selected_route: str = "",
    origin_text: str = "",
    origin_latitude: Optional[float] = None,
    origin_longitude: Optional[float] = None,
    destination_text: str = "",
    destination_latitude: Optional[float] = None,
    destination_longitude: Optional[float] = None,
    limit: int = 5,
) -> dict[str, Any]:
    language = detect_language(query or destination_text)
    extracted_destination = extract_destination(query, routes, destination_text)
    origin = resolve_place(origin_text, routes, origin_latitude, origin_longitude, "Current location")
    destination = resolve_place(extracted_destination, routes, destination_latitude, destination_longitude, extracted_destination or "Destination")

    if destination is None and selected_route:
        return _selected_route_fallback(routes, vehicles, selected_route, query, language, limit)

    matches = find_matching_routes(origin, destination, routes)
    suggestions = _rank_vehicles_for_matches(matches, vehicles, origin, limit)
    answer = format_suggestion_answer(language, origin, destination, suggestions, matches)
    return {
        "language": language,
        "origin": origin,
        "destination": destination,
        "matches": matches[:limit],
        "suggestions": suggestions[:limit],
        "answer": answer,
    }


def find_matching_routes(
    origin: Optional[dict[str, Any]],
    destination: Optional[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if destination is None:
        return []
    matches: list[dict[str, Any]] = []
    for route in routes:
        points = route_points(route, prefer_stops=True)
        if len(points) < 2:
            continue
        board = _nearest_point(origin, points) if origin else None
        alight = _nearest_point(destination, points)
        if not alight:
            continue
        board = board or _nearest_point(points[0], points)
        direction = "forward" if board["index"] <= alight["index"] else "backward"
        strict = (
            board["distance_meters"] <= WALKING_RADIUS_METERS
            and alight["distance_meters"] <= WALKING_RADIUS_METERS
        )
        destination_near = alight["distance_meters"] <= RELAXED_RADIUS_METERS
        route_text = normalize_text(f"{route.get('route', '')} {route.get('name', '')} {' '.join(route.get('landmarks', []))}")
        destination_text = normalize_text(destination.get("name", ""))
        text_match = bool(destination_text and destination_text in route_text)
        if strict or destination_near or text_match:
            score = board["distance_meters"] + alight["distance_meters"] + (0 if strict else 900)
            matches.append({
                "route": route.get("route"),
                "route_name": route.get("name"),
                "city": route.get("city") or infer_city(route.get("polyline", []), route.get("name", "")),
                "zone": route.get("zone", ""),
                "direction": direction,
                "strict": strict,
                "score": round(score, 1),
                "boarding_stop": board,
                "alighting_stop": alight,
                "walking_distance_meters": round(board["distance_meters"], 0),
                "destination_walk_meters": round(alight["distance_meters"], 0),
                "fare_pesos": estimate_fare(points, board["index"], alight["index"]),
            })
    matches.sort(key=lambda item: (not item["strict"], item["score"], item["route_name"] or ""))
    return matches[:12]


def route_points(route: dict[str, Any], prefer_stops: bool = False) -> list[dict[str, Any]]:
    meta = route_metadata(str(route.get("route", "")))
    stops = meta.get("stops") if prefer_stops else None
    stops = stops or route.get("stops") or []
    points = stops if stops else route.get("polyline") or []
    result = []
    for index, point in enumerate(points):
        if not _valid_coord(point):
            continue
        result.append({
            "index": int(point.get("stop_id", index)) if isinstance(point, dict) else index,
            "name": point.get("name", f"Stop {index + 1}") if isinstance(point, dict) else f"Stop {index + 1}",
            "latitude": float(point["latitude"] if isinstance(point, dict) else point[0]),
            "longitude": float(point["longitude"] if isinstance(point, dict) else point[1]),
        })
    return result


def estimate_fare(points: list[dict[str, Any]], board_index: int, alight_index: int) -> int:
    start = min(board_index, alight_index)
    end = max(board_index, alight_index)
    distance = 0.0
    for left, right in zip(points[start:end], points[start + 1:end + 1]):
        distance += haversine_meters(left["latitude"], left["longitude"], right["latitude"], right["longitude"])
    km = distance / 1000.0
    return int(round(max(13.0, 13.0 + max(0.0, km - 4.0) * 1.8)))


def format_suggestion_answer(
    language: str,
    origin: Optional[dict[str, Any]],
    destination: Optional[dict[str, Any]],
    suggestions: list[dict[str, Any]],
    matches: list[dict[str, Any]],
) -> str:
    if not destination:
        if language == "tl":
            return "Sabihin mo ang destinasyon mo para mahanap ko ang tamang ruta."
        if language == "ceb":
            return "Isulti ang imong destinasyon para pangitaon nako ang sakto nga ruta."
        if language == "ilo":
            return "Isugid ang destinasyon mo para mapangita ko ang maayo nga ruta."
        if language == "ilocano":
            return "Ibagam ti papanam tapno mabirok ko ti umiso a ruta."
        return "Please tell me your destination so I can search every route."
    if not matches:
        if language == "tl":
            return f"Wala pa akong nakitang ruta malapit sa {destination['name']}. Subukan ang kalapit na landmark o endpoint."
        if language == "ceb":
            return f"Wala pa koy nakitang ruta duol sa {destination['name']}. Sulayi ang duol nga landmark o endpoint."
        if language == "ilo":
            return f"Wala pa ako sang nakita nga ruta malapit sa {destination['name']}. Tilawi ang lapit nga landmark o endpoint."
        if language == "ilocano":
            return f"Awan pay nakita a ruta nga asideg iti {destination['name']}. Padasem ti asideg a landmark wenno endpoint."
        return f"I could not find a route near {destination['name']} yet. Try a nearby landmark or route endpoint."
    if not suggestions:
        route_names = ", ".join(f"{match['route']} {match['route_name']}" for match in matches[:3])
        if language == "tl":
            return f"May nahanap akong ruta malapit sa {destination['name']} ({route_names}), pero wala pang active na PUV na nagre-report ngayon."
        if language == "ceb":
            return f"Nakita nako ang mga ruta duol sa {destination['name']} ({route_names}), pero walay active nga PUV nga nag-report karon."
        if language == "ilo":
            return f"May nakita ako nga mga ruta malapit sa {destination['name']} ({route_names}), pero wala pa sang active nga PUV subong."
        if language == "ilocano":
            return f"Adda dagiti ruta nga asideg iti {destination['name']} ({route_names}), ngem awan pay active nga PUV ita."
        return f"I found matching routes near {destination['name']} ({route_names}), but no active PUVs are reporting on them right now."
    best = suggestions[0]
    if language == "tl":
        return (
            f"Pinakamagandang sakyan: Ruta {best['route']} ({best['route_name']}), PUV {best['vehicle_id']}. "
            f"Sumakay malapit sa {best['boarding_stop']['name']} at bumaba malapit sa {best['alighting_stop']['name']}. "
            f"Nasa {best['distance_km']:.1f} km ito mula sa iyo at darating sa ~{best['eta_minutes']:.0f} minuto. "
            f"Tantyang pamasahe: PHP {best['fare_pesos']}."
        )
    if language == "ceb":
        return (
            f"Pinakamaayong sakyan: Ruta {best['route']} ({best['route_name']}), PUV {best['vehicle_id']}. "
            f"Sakay duol sa {best['boarding_stop']['name']} ug naog duol sa {best['alighting_stop']['name']}. "
            f"Mga {best['distance_km']:.1f} km kini gikan nimo ug moabot sa ~{best['eta_minutes']:.0f} minuto. "
            f"Banabana nga plete: PHP {best['fare_pesos']}."
        )
    if language == "ilo":
        return (
            f"Pinakamaayo nga sakyan: Ruta {best['route']} ({best['route_name']}), PUV {best['vehicle_id']}. "
            f"Sakay malapit sa {best['boarding_stop']['name']} kag naog malapit sa {best['alighting_stop']['name']}. "
            f"Mga {best['distance_km']:.1f} km ini halin sa imo kag maabot sa ~{best['eta_minutes']:.0f} minuto. "
            f"Ginalantaw nga plete: PHP {best['fare_pesos']}."
        )
    if language == "ilocano":
        return (
            f"Nasayaat a pagpilian: Ruta {best['route']} ({best['route_name']}), PUV {best['vehicle_id']}. "
            f"Sakay iti asideg ti {best['boarding_stop']['name']} ket bumaba iti asideg ti {best['alighting_stop']['name']}. "
            f"Agarup {best['distance_km']:.1f} km manipud kenka ken umay iti ~{best['eta_minutes']:.0f} minuto. "
            f"Karkulo a bayad: PHP {best['fare_pesos']}."
        )
    base = (
        f"Best option: Route {best['route']} ({best['route_name']}), Vehicle {best['vehicle_id']}. "
        f"Board near {best['boarding_stop']['name']} and alight near {best['alighting_stop']['name']}. "
        f"It is about {best['distance_km']:.1f} km from you, arriving in ~{best['eta_minutes']:.0f} minutes. "
        f"Estimated fare: PHP {best['fare_pesos']}."
    )
    return base


def _selected_route_fallback(
    routes: list[dict[str, Any]],
    vehicles: list[dict[str, Any]],
    selected_route: str,
    query: str,
    language: str,
    limit: int,
) -> dict[str, Any]:
    route = next((item for item in routes if item.get("route") == selected_route), None)
    route_vehicles = [vehicle for vehicle in vehicles if vehicle.get("route") == selected_route]
    route_vehicles.sort(key=lambda vehicle: (_tier_penalty(vehicle.get("tier")), float(vehicle.get("eta_minutes") or 999)))
    suggestions = []
    for vehicle in route_vehicles[:limit]:
        suggestions.append({
            "vehicle_id": vehicle.get("vehicle_id"),
            "route": selected_route,
            "route_name": route.get("name") if route else selected_route,
            "city": route.get("city") if route else "",
            "eta_minutes": round(float(vehicle.get("eta_minutes") or 0), 1),
            "distance_meters": None,
            "distance_km": 0.0,
            "fare_pesos": 13,
            "occupancy": vehicle.get("occupancy"),
            "capacity": vehicle.get("capacity"),
            "tier": vehicle.get("tier"),
            "status": vehicle.get("status", "active"),
            "direction": vehicle.get("direction"),
            "boarding_stop": {"name": f"Route {selected_route} next stop"},
            "alighting_stop": {"name": "selected corridor"},
        })
    if suggestions:
        best = suggestions[0]
        action = "board" if best["tier"] in {"green", "yellow"} else "wait for the next less crowded PUV"
        answer = _translate(language, f"For Route {selected_route}, {action}: Vehicle {best['vehicle_id']} has ETA {best['eta_minutes']} minutes and {best['occupancy']}/{best['capacity']} riders.")
    else:
        answer = _translate(language, f"No live vehicles are reporting for Route {selected_route} yet.")
    return {
        "language": language,
        "origin": None,
        "destination": None,
        "matches": [],
        "suggestions": suggestions,
        "answer": answer,
    }


def _rank_vehicles_for_matches(
    matches: list[dict[str, Any]],
    vehicles: list[dict[str, Any]],
    origin: Optional[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    suggestions = []
    for match in matches:
        route_vehicles = [
            vehicle for vehicle in vehicles
            if vehicle.get("route") == match["route"] and vehicle.get("status", "active") != "idle"
        ]
        strict_vehicles = [
            vehicle for vehicle in route_vehicles
            if _vehicle_can_reach_boarding_stop(vehicle, match)
        ]
        candidates = strict_vehicles or route_vehicles
        for vehicle in candidates:
            if not _valid_coord(vehicle):
                continue
            target = origin or match["boarding_stop"]
            distance = haversine_meters(
                float(vehicle["latitude"]),
                float(vehicle["longitude"]),
                float(target["latitude"]),
                float(target["longitude"]),
            )
            eta = calculate_eta_minutes(distance, vehicle.get("speed_kph"))
            suggestions.append({
                "vehicle_id": vehicle.get("vehicle_id"),
                "route": match["route"],
                "route_name": match["route_name"],
                "city": match["city"],
                "zone": match["zone"],
                "eta_minutes": eta,
                "distance_meters": round(distance, 0),
                "distance_km": round(distance / 1000.0, 2),
                "fare_pesos": match["fare_pesos"],
                "occupancy": vehicle.get("occupancy"),
                "capacity": vehicle.get("capacity"),
                "tier": vehicle.get("tier"),
                "status": vehicle.get("status", "active"),
                "direction": vehicle.get("direction"),
                "speed_kph": vehicle.get("speed_kph") or DEFAULT_SPEED_KPH,
                "boarding_stop": match["boarding_stop"],
                "alighting_stop": match["alighting_stop"],
                "walking_distance_meters": match["walking_distance_meters"],
                "destination_walk_meters": match["destination_walk_meters"],
            })
    suggestions.sort(key=lambda item: (item["eta_minutes"], _tier_penalty(item.get("tier")), item["distance_km"]))
    return suggestions[:limit]


def _vehicle_can_reach_boarding_stop(vehicle: dict[str, Any], match: dict[str, Any]) -> bool:
    direction = vehicle.get("direction")
    if direction not in {"forward", "backward"}:
        return True
    route_points_for_vehicle = ROUTE_METADATA.get(match["route"], {}).get("stops")
    if not route_points_for_vehicle:
        return True
    vehicle_point = _nearest_point(vehicle, route_points_for_vehicle)
    if not vehicle_point:
        return True
    board_index = match["boarding_stop"]["index"]
    if direction == "forward":
        return vehicle_point["index"] <= board_index
    return vehicle_point["index"] >= board_index


def _nearest_point(target: Optional[dict[str, Any]], points: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not target or not _valid_coord(target):
        return None
    best = None
    best_distance = float("inf")
    for point in points:
        distance = haversine_meters(
            float(target["latitude"]),
            float(target["longitude"]),
            float(point["latitude"]),
            float(point["longitude"]),
        )
        if distance < best_distance:
            best_distance = distance
            best = point
    if best is None:
        return None
    return {
        **best,
        "distance_meters": round(best_distance, 1),
    }


def _best_place_text_match(normalized_query: str, places: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    if not normalized_query:
        return None
    best: tuple[int, Optional[dict[str, Any]]] = (0, None)
    for place in places:
        aliases = [place["name"], *(place.get("aliases") or [])]
        for alias in aliases:
            normalized_alias = normalize_text(alias)
            if not normalized_alias:
                continue
            score = 0
            if normalized_alias == normalized_query:
                score = 200 + len(normalized_alias)
            elif normalized_alias in normalized_query:
                score = 150 + len(normalized_alias)
            elif normalized_query in normalized_alias:
                score = 80 + len(normalized_query)
            elif all(token in normalized_alias for token in normalized_query.split()):
                score = 60 + len(normalized_query)
            if score > best[0]:
                best = (score, place)
    return best[1]


def _clean_destination(value: str) -> str:
    value = re.sub(r"\b(from here|right now|please|pls|po|lang|diri|dito|gikan diri)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ?.,")
    return value.title() if value else ""


def _valid_coord(point: Any) -> bool:
    try:
        lat = float(point["latitude"] if isinstance(point, dict) else point[0])
        lon = float(point["longitude"] if isinstance(point, dict) else point[1])
    except (KeyError, IndexError, TypeError, ValueError):
        return False
    return -90 <= lat <= 90 and -180 <= lon <= 180 and not (lat == 0 and lon == 0)


def _dedupe_places(places: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, int]] = set()
    deduped = []
    for place in places:
        key = (
            normalize_text(place["name"]),
            round(float(place["latitude"]) * 10000),
            round(float(place["longitude"]) * 10000),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(place)
    return deduped


def _tier_penalty(tier: Optional[str]) -> int:
    return {
        "green": 0,
        "yellow": 1,
        "red": 2,
        "blinking_red": 3,
    }.get(tier or "", 4)


def _translate(language: str, english: str) -> str:
    if language == "tl":
        replacements = {
            "Best option": "Pinakamagandang sakyan",
            "Route": "Ruta",
            "Vehicle": "PUV",
            "Board near": "Sumakay malapit sa",
            "and alight near": "at bumaba malapit sa",
            "It is about": "Nasa",
            "from you, arriving in": "mula sa iyo, darating sa",
            "minutes": "minuto",
            "Estimated fare": "Tantyang pamasahe",
            "Please tell me your destination so I can search every route.": "Sabihin mo ang destinasyon mo para mahanap ko ang tamang ruta.",
        }
    elif language == "ceb":
        replacements = {
            "Best option": "Pinakamaayong sakyan",
            "Route": "Ruta",
            "Vehicle": "PUV",
            "Board near": "Sakay duol sa",
            "and alight near": "ug naog duol sa",
            "It is about": "Mga",
            "from you, arriving in": "gikan nimo, moabot sa",
            "minutes": "minuto",
            "Estimated fare": "Banabana nga plete",
            "Please tell me your destination so I can search every route.": "Isulti ang imong destinasyon para pangitaon nako ang sakto nga ruta.",
        }
    elif language == "ilo":
        replacements = {
            "Best option": "Pinakamaayo nga sakyan",
            "Route": "Ruta",
            "Vehicle": "PUV",
            "Board near": "Sakay malapit sa",
            "and alight near": "kag naog malapit sa",
            "Estimated fare": "Ginalantaw nga plete",
        }
    elif language == "ilocano":
        replacements = {
            "Best option": "Nasayaat a pagpilian",
            "Route": "Ruta",
            "Vehicle": "PUV",
            "Estimated fare": "Karkulo a bayad",
        }
    else:
        replacements = {}
    translated = english
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated
