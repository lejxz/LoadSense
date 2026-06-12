from __future__ import annotations

import math
import re
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Iterable, Optional


WALKING_RADIUS_METERS = 500.0
RELAXED_RADIUS_METERS = 1500.0
DEFAULT_SPEED_KPH = 30.0
PHOTON_SEARCH_URL = "https://photon.komoot.io/api/"


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
    {
        "route": "SG-BTL",
        "name": "Singapore Downtown Line: Bukit Panjang - Expo",
        "city": "Singapore",
        "zone": "Downtown Line",
        "type": "Metro",
        "stops": [
            _stop("Bukit Panjang", 1.3790, 103.7615),
            _stop("Botanic Gardens", 1.3224, 103.8154),
            _stop("Stevens", 1.3200, 103.8260),
            _stop("Newton", 1.3123, 103.8379),
            _stop("Bugis", 1.3007, 103.8560),
            _stop("Chinatown", 1.2844, 103.8434),
            _stop("MacPherson", 1.3266, 103.8904),
            _stop("Tampines", 1.3547, 103.9437),
            _stop("Expo", 1.3352, 103.9629),
        ],
    },
    {
        "route": "SG-EWL",
        "name": "Singapore East West Line: Jurong East - Changi Airport",
        "city": "Singapore",
        "zone": "East West Line",
        "type": "Metro",
        "stops": [
            _stop("Jurong East", 1.3331, 103.7420),
            _stop("Clementi", 1.3151, 103.7652),
            _stop("Buona Vista", 1.3072, 103.7904),
            _stop("Tiong Bahru", 1.2862, 103.8271),
            _stop("City Hall", 1.2931, 103.8521),
            _stop("Paya Lebar", 1.3182, 103.8930),
            _stop("Bedok", 1.3240, 103.9302),
            _stop("Tanah Merah", 1.3273, 103.9465),
            _stop("Changi Airport", 1.3574, 103.9879),
        ],
    },
    {
        "route": "HK-ISL",
        "name": "Hong Kong Island Line: Kennedy Town - Chai Wan",
        "city": "Hong Kong",
        "zone": "Island Line",
        "type": "Metro",
        "stops": [
            _stop("Kennedy Town", 22.2812, 114.1288),
            _stop("HKU", 22.2836, 114.1355),
            _stop("Sheung Wan", 22.2869, 114.1524),
            _stop("Central", 22.2819, 114.1582),
            _stop("Admiralty", 22.2798, 114.1648),
            _stop("Wan Chai", 22.2770, 114.1734),
            _stop("Causeway Bay", 22.2802, 114.1858),
            _stop("North Point", 22.2911, 114.2004),
            _stop("Chai Wan", 22.2647, 114.2370),
        ],
    },
    {
        "route": "JPN-YMN",
        "name": "Tokyo Yamanote Loop: Shinjuku - Tokyo - Ueno",
        "city": "Tokyo",
        "zone": "Yamanote",
        "type": "Rail",
        "stops": [
            _stop("Shinjuku", 35.6909, 139.7003),
            _stop("Shibuya", 35.6580, 139.7016),
            _stop("Shinagawa", 35.6285, 139.7388),
            _stop("Tokyo Station", 35.6812, 139.7671),
            _stop("Akihabara", 35.6984, 139.7730),
            _stop("Ueno", 35.7138, 139.7770),
            _stop("Ikebukuro", 35.7289, 139.7104),
        ],
    },
]


PLACE_DATABASE: list[dict[str, Any]] = [
    {"name": "Cebu City", "city": "Cebu", "latitude": 10.3157, "longitude": 123.8854, "aliases": ["cebu", "cebu city"], "kind": "city"},
    {"name": "Mandaue City", "city": "Cebu", "latitude": 10.3333, "longitude": 123.9333, "aliases": ["mandaue", "mandaue city"], "kind": "city"},
    {"name": "Lapu-Lapu City", "city": "Cebu", "latitude": 10.3103, "longitude": 123.9494, "aliases": ["lapu lapu", "lapu-lapu", "mactan"], "kind": "city"},
    {"name": "Talisay City Cebu", "city": "Cebu", "latitude": 10.2447, "longitude": 123.8494, "aliases": ["talisay", "talisay cebu", "talisay city"], "kind": "city"},
    {"name": "Minglanilla", "city": "Cebu", "latitude": 10.2447, "longitude": 123.7964, "aliases": ["minglanilla cebu", "mingla"], "kind": "town"},
    {"name": "Naga City Cebu", "city": "Cebu", "latitude": 10.2090, "longitude": 123.7580, "aliases": ["naga", "naga cebu", "naga city"], "kind": "city"},
    {"name": "San Fernando Cebu", "city": "Cebu", "latitude": 10.1625, "longitude": 123.7076, "aliases": ["san fernando", "san fernando cebu"], "kind": "town"},
    {"name": "Carcar City", "city": "Cebu", "latitude": 10.1061, "longitude": 123.6402, "aliases": ["carcar", "carcar cebu"], "kind": "city"},
    {"name": "Consolacion", "city": "Cebu", "latitude": 10.3776, "longitude": 123.9575, "aliases": ["consolacion cebu"], "kind": "town"},
    {"name": "Liloan", "city": "Cebu", "latitude": 10.3991, "longitude": 123.9992, "aliases": ["liloan cebu"], "kind": "town"},
    {"name": "Compostela Cebu", "city": "Cebu", "latitude": 10.4550, "longitude": 124.0106, "aliases": ["compostela"], "kind": "town"},
    {"name": "Danao City", "city": "Cebu", "latitude": 10.5208, "longitude": 124.0275, "aliases": ["danao", "danao cebu"], "kind": "city"},
    {"name": "Cordova Cebu", "city": "Cebu", "latitude": 10.2523, "longitude": 123.9495, "aliases": ["cordova"], "kind": "town"},
    {"name": "Toledo City", "city": "Cebu", "latitude": 10.3773, "longitude": 123.6386, "aliases": ["toledo", "toledo cebu"], "kind": "city"},
    {"name": "Balamban", "city": "Cebu", "latitude": 10.5039, "longitude": 123.7153, "aliases": ["balamban cebu"], "kind": "town"},
    {"name": "Dumanjug", "city": "Cebu", "latitude": 10.0570, "longitude": 123.4365, "aliases": ["dumanjug cebu"], "kind": "town"},
    {"name": "Barili", "city": "Cebu", "latitude": 10.1150, "longitude": 123.5103, "aliases": ["barili cebu"], "kind": "town"},
    {"name": "Moalboal", "city": "Cebu", "latitude": 9.9436, "longitude": 123.3996, "aliases": ["moalboal cebu"], "kind": "town"},
    {"name": "Samboan", "city": "Cebu", "latitude": 9.5276, "longitude": 123.3068, "aliases": ["samboan cebu"], "kind": "town"},
    {"name": "Oslob", "city": "Cebu", "latitude": 9.5211, "longitude": 123.4315, "aliases": ["oslob cebu"], "kind": "town"},
    {"name": "Bogo City", "city": "Cebu", "latitude": 11.0517, "longitude": 124.0055, "aliases": ["bogo", "bogo cebu"], "kind": "city"},
    {"name": "Daanbantayan", "city": "Cebu", "latitude": 11.2468, "longitude": 124.0160, "aliases": ["daan bantayan", "daanbantayan cebu"], "kind": "town"},
    {"name": "Basak Cebu", "city": "Cebu City", "latitude": 10.2847, "longitude": 123.8647, "aliases": ["basak", "basak cebu", "basak pardo", "basak cebu city"], "kind": "barangay"},
    {"name": "Basak Lapu-Lapu", "city": "Lapu-Lapu City", "latitude": 10.2936, "longitude": 123.9634, "aliases": ["basak lapu lapu", "basak mactan"], "kind": "barangay"},
    {"name": "Pardo", "city": "Cebu City", "latitude": 10.2822, "longitude": 123.8527, "aliases": ["pardo cebu"], "kind": "barangay"},
    {"name": "Bulacao", "city": "Cebu City", "latitude": 10.2723, "longitude": 123.8500, "aliases": ["bulacao cebu"], "kind": "barangay"},
    {"name": "Punta Princesa", "city": "Cebu City", "latitude": 10.2878, "longitude": 123.8748, "aliases": ["punta", "punta princesa cebu"], "kind": "barangay"},
    {"name": "Tabunok", "city": "Talisay City", "latitude": 10.2651, "longitude": 123.8429, "aliases": ["talisay tabunok", "tabunok talisay"], "kind": "barangay"},
    {"name": "Guadalupe Cebu", "city": "Cebu City", "latitude": 10.3140, "longitude": 123.8830, "aliases": ["guadalupe", "guadalupe cebu"], "kind": "barangay"},
    {"name": "Lahug", "city": "Cebu City", "latitude": 10.3370, "longitude": 123.8995, "aliases": ["lahug cebu"], "kind": "barangay"},
    {"name": "Talamban", "city": "Cebu City", "latitude": 10.3700, "longitude": 123.9120, "aliases": ["talamban cebu"], "kind": "barangay"},
    {"name": "Colon Street", "city": "Cebu City", "latitude": 10.2964, "longitude": 123.8997, "aliases": ["colon"], "kind": "landmark"},
    {"name": "Carbon Market", "city": "Cebu City", "latitude": 10.2927, "longitude": 123.9006, "aliases": ["carbon", "carbon market"], "kind": "landmark"},
    {"name": "Fuente Osmena Circle", "city": "Cebu City", "latitude": 10.3093, "longitude": 123.8930, "aliases": ["fuente", "fuente osmena"], "kind": "landmark"},
    {"name": "Cebu IT Park", "city": "Cebu City", "latitude": 10.3306, "longitude": 123.9067, "aliases": ["it park", "cebu it park"], "kind": "landmark"},
    {"name": "South Bus Terminal Cebu", "city": "Cebu City", "latitude": 10.2948, "longitude": 123.8938, "aliases": ["south bus", "south bus terminal", "cebu south bus terminal"], "kind": "terminal"},
    {"name": "North Bus Terminal Cebu", "city": "Mandaue City", "latitude": 10.3358, "longitude": 123.9324, "aliases": ["north bus", "north bus terminal", "cebu north bus terminal"], "kind": "terminal"},
]


LANDMARKS: list[dict[str, Any]] = [
    {"name": "Ayala Center Cebu", "city": "Cebu City", "latitude": 10.3173, "longitude": 123.9058, "aliases": ["ayala", "ayala center"]},
    {"name": "SM City Cebu", "city": "Cebu City", "latitude": 10.3115, "longitude": 123.9183, "aliases": ["sm cebu", "sm city"]},
    {"name": "Parkmall Mandaue", "city": "Mandaue", "latitude": 10.3337, "longitude": 123.9336, "aliases": ["parkmall"]},
    {"name": "SM Seaside City Cebu", "city": "Cebu City", "latitude": 10.2810, "longitude": 123.8817, "aliases": ["sm seaside", "seaside"]},
    {"name": "Changi Airport", "city": "Singapore", "latitude": 1.3574, "longitude": 103.9879, "aliases": ["changi", "singapore airport"]},
    {"name": "Marina Bay", "city": "Singapore", "latitude": 1.2830, "longitude": 103.8600, "aliases": ["marina bay sands", "mbs"]},
    {"name": "Central Hong Kong", "city": "Hong Kong", "latitude": 22.2819, "longitude": 114.1582, "aliases": ["central", "hong kong central"]},
    {"name": "Shinjuku Station", "city": "Tokyo", "latitude": 35.6909, "longitude": 139.7003, "aliases": ["shinjuku"]},
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
    "ceb": ["asa", "paingon", "padung", "gikan", "unsa", "sakay", "dyip", "diri", "jeep"],
    "tl": ["saan", "papunta", "pumunta", "daan", "byahe", "sakay", "dito", "dyip", "jeep"],
    "ilo": ["diin", "pakadto", "sakyan", "jeep"],
    "ilocano": ["sadino", "mapan", "lugan"],
    "es": ["donde", "como", "tomar", "ruta", "autobus", "llegar", "hacia"],
    "ja": ["eki", "densha", "basu", "doko", "made", "iku"],
}


DESTINATION_PATTERNS = [
    r"(?:destination is|destination|destinasyon|padulngan|adtoan)\s+(.+)",
    r"(?:need to go to|i need to go to|i want to go to|going to)\s+(.+)",
    r"(?:which .*? should i take to reach|which .*? should i take to get to|what .*? should i take to reach)\s+(.+)",
    r"(?:how do i get to|how to get to|which .*? to|what .*? goes to|route to|going to|go to|reach|towards?|to)\s+(.+)",
    r"(?:saan .*? papunta sa|paano pumunta sa|papunta sa|papuntang|punta sa|daan sa|byahe sa)\s+(.+)",
    r"(?:asa .*? paingon sa|unsa .*? paingon sa|paingon sa|padung sa|punta sa)\s+(.+)",
    r"(?:diin .*? pakadto sa|pakadto sa)\s+(.+)",
    r"(?:sadino .*? mapan iti|mapan iti)\s+(.+)",
]


ORIGIN_PATTERNS = [
    r"(?:my current location is at|my current location is|current location is at|current location is|i am at|im at|i'm at|from|gikan sa|gikan)\s+(.+?)(?:\s+i need|\s+i want|\s+what|\s+which|\s+how|\s+to reach|\s+going to|$)",
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
    if "singapore" in name:
        return "Singapore"
    if "hong kong" in name:
        return "Hong Kong"
    if "tokyo" in name:
        return "Tokyo"
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
    if 1.2 <= lat <= 1.45 and 103.6 <= lon <= 104.1:
        return "Singapore"
    if 22.15 <= lat <= 22.45 and 113.9 <= lon <= 114.35:
        return "Hong Kong"
    if 35.55 <= lat <= 35.85 and 139.55 <= lon <= 139.9:
        return "Tokyo"
    return "Philippines"


def build_place_index(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    places: list[dict[str, Any]] = []
    for place in PLACE_DATABASE:
        places.append({
            "name": place["name"],
            "city": place["city"],
            "latitude": place["latitude"],
            "longitude": place["longitude"],
            "aliases": place.get("aliases", []),
            "kind": place.get("kind", "place"),
        })
    for landmark in LANDMARKS:
        places.append({
            "name": landmark["name"],
            "city": landmark["city"],
            "latitude": landmark["latitude"],
            "longitude": landmark["longitude"],
            "aliases": landmark.get("aliases", []),
            "kind": landmark.get("kind", "landmark"),
        })
    for route in routes:
        city = route.get("city") or infer_city(route.get("polyline", []), route.get("name", ""))
        points = route_points(route, prefer_stops=True)
        center = _route_center(points)
        if center:
            places.append({
                "name": f"Route {route.get('route')}",
                "city": city,
                "route": route.get("route"),
                "latitude": center["latitude"],
                "longitude": center["longitude"],
                "aliases": [
                    str(route.get("route", "")),
                    str(route.get("name", "")),
                    f"{route.get('route', '')} {route.get('name', '')}",
                ],
                "kind": "route",
            })
        for stop in points:
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


def search_places(routes: list[dict[str, Any]], query: str = "", limit: int = 12, include_remote: bool = True) -> list[dict[str, Any]]:
    places = build_place_index(routes)
    needle = normalize_text(query or "")
    if not needle:
        return sorted(places, key=_place_sort_key)[:limit]
    scored: list[tuple[int, dict[str, Any]]] = []
    for place in places:
        haystack = " ".join([place["name"], place.get("city", ""), place.get("route", ""), *(place.get("aliases") or [])])
        normalized = normalize_text(haystack)
        score = _text_match_score(needle, normalized)
        if score:
            score += _place_kind_boost(place, needle)
            scored.append((score, place))
    scored.sort(key=lambda item: (-item[0], _place_sort_key(item[1])))
    local_results = [item[1] for item in scored[:limit]]
    if not include_remote or len(needle) < 2:
        return local_results
    remote_results = search_remote_places(query, max(0, limit - len(local_results) + 4))
    return _dedupe_places([*local_results, *remote_results])[:limit]


def search_remote_places(query: str, limit: int = 8) -> list[dict[str, Any]]:
    if limit <= 0:
        return []
    params = urllib.parse.urlencode({"q": query, "limit": min(limit, 12), "lang": "en"})
    request = urllib.request.Request(
        f"{PHOTON_SEARCH_URL}?{params}",
        headers={
            "User-Agent": "LoadSense/1.0 student-demo location search",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=1.8) as response:
            payload = response.read().decode("utf-8")
    except (OSError, urllib.error.URLError, TimeoutError, ValueError):
        return []
    try:
        import json

        features = json.loads(payload).get("features", [])
    except Exception:
        return []
    places = []
    for feature in features:
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") or []
        if len(coordinates) < 2:
            continue
        name = properties.get("name") or properties.get("street") or properties.get("city")
        if not name:
            continue
        city = properties.get("city") or properties.get("town") or properties.get("village") or properties.get("county") or properties.get("country") or ""
        country = properties.get("country") or ""
        kind = _photon_kind(properties)
        aliases = [
            value for value in [
                properties.get("city"),
                properties.get("town"),
                properties.get("village"),
                properties.get("state"),
                properties.get("country"),
                properties.get("postcode"),
            ]
            if value and value != name
        ]
        places.append({
            "name": name,
            "city": city or country or "OpenStreetMap",
            "country": country,
            "latitude": float(coordinates[1]),
            "longitude": float(coordinates[0]),
            "aliases": aliases,
            "kind": kind,
            "source": "photon_osm",
            "osm_id": properties.get("osm_id"),
            "osm_type": properties.get("osm_type"),
        })
    return places


def extract_destination(query: str, routes: list[dict[str, Any]], explicit_destination: str = "") -> str:
    if explicit_destination.strip():
        return explicit_destination.strip()
    normalized = normalize_text(query)
    for pattern in DESTINATION_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            candidate = _clean_destination(match.group(1))
            if candidate:
                return candidate
    places = build_place_index(routes)
    matched_place = _best_place_text_match(normalized, places)
    if matched_place:
        return matched_place["name"]
    return ""


def extract_origin(query: str, explicit_origin: str = "") -> str:
    if explicit_origin.strip() and normalize_text(explicit_origin) not in {"current location", "my location", "here"}:
        return explicit_origin.strip()
    normalized = normalize_text(query)
    for pattern in ORIGIN_PATTERNS:
        match = re.search(pattern, normalized)
        if match:
            return _clean_place_phrase(match.group(1))
    return explicit_origin.strip()


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
    extracted_origin = extract_origin(query, origin_text)
    origin = resolve_place(extracted_origin, routes, origin_latitude, origin_longitude, "Current location")
    destination = resolve_place(extracted_destination, routes, destination_latitude, destination_longitude, extracted_destination or "Destination")

    if destination is None and selected_route:
        return _selected_route_fallback(routes, vehicles, selected_route, query, language, limit)

    matches = find_matching_routes(origin, destination, routes)
    if not matches and origin and destination:
        matches = find_multi_leg_routes(origin, destination, routes)
        
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
        
    if origin and destination:
        dist_od = haversine_meters(origin["latitude"], origin["longitude"], destination["latitude"], destination["longitude"])
        if dist_od > 100000:
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
        
        if board["distance_meters"] > RELAXED_RADIUS_METERS or alight["distance_meters"] > RELAXED_RADIUS_METERS:
            continue
            
        direction = "forward" if board["index"] <= alight["index"] else "backward"
        strict = (
            board["distance_meters"] <= WALKING_RADIUS_METERS
            and alight["distance_meters"] <= WALKING_RADIUS_METERS
        )
        
        score = board["distance_meters"] + alight["distance_meters"] + (0 if strict else 1000)
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

def find_multi_leg_routes(
    origin: Optional[dict[str, Any]],
    destination: Optional[dict[str, Any]],
    routes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not origin or not destination:
        return []
    
    leg1_candidates = []
    leg2_candidates = []
    
    for route in routes:
        points = route_points(route, prefer_stops=True)
        if len(points) < 2:
            continue
            
        board = _nearest_point(origin, points)
        if board and board["distance_meters"] <= RELAXED_RADIUS_METERS:
            leg1_candidates.append((route, points, board))
            
        alight = _nearest_point(destination, points)
        if alight and alight["distance_meters"] <= RELAXED_RADIUS_METERS:
            leg2_candidates.append((route, points, alight))
            
    matches = []
    
    for r1, pts1, board1 in leg1_candidates:
        for r2, pts2, alight2 in leg2_candidates:
            if r1.get("route") == r2.get("route"):
                continue
                
            best_transfer = None
            best_transfer_dist = float('inf')
            
            for p1 in pts1:
                for p2 in pts2:
                    dist = haversine_meters(p1["latitude"], p1["longitude"], p2["latitude"], p2["longitude"])
                    if dist < 500 and dist < best_transfer_dist:
                        best_transfer_dist = dist
                        best_transfer = (p1, p2)
                        
            if best_transfer:
                p1, p2 = best_transfer
                direction1 = "forward" if board1["index"] <= p1["index"] else "backward"
                direction2 = "forward" if p2["index"] <= alight2["index"] else "backward"
                
                score = board1["distance_meters"] + alight2["distance_meters"] + best_transfer_dist + 2000
                matches.append({
                    "legs": [
                        {
                            "route": r1.get("route"),
                            "route_name": r1.get("name"),
                            "direction": direction1,
                            "boarding_stop": board1,
                            "alighting_stop": p1,
                        },
                        {
                            "route": r2.get("route"),
                            "route_name": r2.get("name"),
                            "direction": direction2,
                            "boarding_stop": p2,
                            "alighting_stop": alight2,
                        }
                    ],
                    "route": f"{r1.get('route')} to {r2.get('route')}",
                    "route_name": f"Transfer at {p1['name']}",
                    "city": r1.get("city") or infer_city(r1.get("polyline", []), r1.get("name", "")),
                    "zone": r1.get("zone", ""),
                    "direction": "multi",
                    "strict": False,
                    "score": round(score, 1),
                    "boarding_stop": board1,
                    "alighting_stop": alight2,
                    "transfer_stop": p1,
                    "walking_distance_meters": round(board1["distance_meters"], 0),
                    "destination_walk_meters": round(alight2["distance_meters"], 0),
                    "transfer_walk_meters": round(best_transfer_dist, 0),
                    "fare_pesos": estimate_fare(pts1, board1["index"], p1["index"]) + estimate_fare(pts2, p2["index"], alight2["index"]),
                })
                
    matches.sort(key=lambda item: item["score"])
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
    return int(round(max(13.0, 13.0 + max(0.0, km - 4.0) * 2.25)))


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
    crowd_note = ""
    if best.get("tier") in {"red", "blinking_red"}:
        crowd_note = " This PUV is crowded; wait for a green or yellow option if you can."
    elif len(suggestions) > 1:
        crowd_note = f" Next option: {suggestions[1]['vehicle_id']} on Route {suggestions[1]['route']}."
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
        f"Destination: {destination['name']}\n"
        f"Recommended route: {best['route']} - {best['route_name']}\n"
        f"PUV to board: {best['vehicle_id']} ({best.get('tier', 'active').replace('_', ' ')})\n"
        f"Board near: {best['boarding_stop']['name']}\n"
        f"Alight near: {best['alighting_stop']['name']}\n"
        f"Arrival: ~{best['eta_minutes']:.0f} min ({best['distance_km']:.1f} km from you)\n"
        f"Estimated fare: PHP {best['fare_pesos']}.{crowd_note}"
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
        route_id = match["legs"][0]["route"] if "legs" in match else match["route"]
        boarding_stop = match["legs"][0]["boarding_stop"] if "legs" in match else match["boarding_stop"]
        alighting_stop = match["legs"][-1]["alighting_stop"] if "legs" in match else match["alighting_stop"]
        
        route_vehicles = [
            vehicle for vehicle in vehicles
            if vehicle.get("route") == route_id and vehicle.get("status", "active") != "idle"
        ]
        strict_vehicles = [
            vehicle for vehicle in route_vehicles
            if _vehicle_can_reach_boarding_stop(vehicle, match)
        ]
        candidates = strict_vehicles or route_vehicles
        
        if not candidates and "legs" in match:
            # If multi-leg and no vehicles, still suggest the route itself
            suggestions.append({
                "vehicle_id": "Any PUV",
                "route": match["route"],
                "route_name": match["route_name"],
                "city": match["city"],
                "zone": match["zone"],
                "eta_minutes": 0,
                "distance_meters": 0,
                "distance_km": 0.0,
                "fare_pesos": match["fare_pesos"],
                "occupancy": 0,
                "capacity": 0,
                "tier": "active",
                "status": "active",
                "direction": match["direction"],
                "speed_kph": DEFAULT_SPEED_KPH,
                "boarding_stop": boarding_stop,
                "alighting_stop": alighting_stop,
                "walking_distance_meters": match["walking_distance_meters"],
                "destination_walk_meters": match["destination_walk_meters"],
                "match_score": match["score"],
                "legs": match.get("legs"),
            })
            continue

        for vehicle in candidates:
            if not _valid_coord(vehicle):
                continue
            target = origin or boarding_stop
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
                "boarding_stop": boarding_stop,
                "alighting_stop": alighting_stop,
                "walking_distance_meters": match["walking_distance_meters"],
                "destination_walk_meters": match["destination_walk_meters"],
                "match_score": match["score"],
                "legs": match.get("legs"),
            })
    suggestions.sort(key=lambda item: (item["match_score"], _tier_penalty(item.get("tier")), item["eta_minutes"], item["distance_km"]))
    return suggestions[:limit]


def _vehicle_can_reach_boarding_stop(vehicle: dict[str, Any], match: dict[str, Any]) -> bool:
    direction = vehicle.get("direction")
    if direction not in {"forward", "backward"}:
        return True
        
    route_id = match["legs"][0]["route"] if "legs" in match else match["route"]
    boarding_stop = match["legs"][0]["boarding_stop"] if "legs" in match else match["boarding_stop"]
    
    route_points_for_vehicle = ROUTE_METADATA.get(route_id, {}).get("stops")
    if not route_points_for_vehicle:
        return True
    vehicle_point = _nearest_point(vehicle, route_points_for_vehicle)
    if not vehicle_point:
        return True
    board_index = boarding_stop.get("index", 0)
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
    index = best.get("index", best.get("stop_id", points.index(best)))
    return {
        **best,
        "index": int(index),
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
            score = _text_match_score(normalized_query, normalized_alias)
            if score:
                score += _place_kind_boost(place, normalized_query)
            if score > best[0]:
                best = (score, place)
    return best[1]


def _text_match_score(needle: str, haystack: str) -> int:
    if not needle or not haystack:
        return 0
    if haystack == needle:
        return 220 + len(haystack)
    if haystack in needle:
        return 165 + len(haystack)
    if needle in haystack:
        return 110 + len(needle)
    tokens = needle.split()
    if tokens and all(token in haystack for token in tokens):
        return 85 + len(needle)
    compact_needle = needle.replace(" ", "")
    compact_haystack = haystack.replace(" ", "")
    if compact_needle and compact_needle in compact_haystack:
        return 75 + len(compact_needle)
    return 0


def _place_kind_boost(place: dict[str, Any], needle: str = "") -> int:
    kind = place.get("kind", "")
    route_like = bool(re.fullmatch(r"(route\s+)?[a-z0-9]{1,4}", needle or ""))
    boosts = {
        "city": 70,
        "town": 68,
        "barangay": 66,
        "terminal": 58,
        "landmark": 54,
        "place": 48,
        "stop": 14,
        "route": 38 if route_like else -45,
    }
    return boosts.get(kind, 0)


def _photon_kind(properties: dict[str, Any]) -> str:
    osm_key = str(properties.get("osm_key") or "").lower()
    osm_value = str(properties.get("osm_value") or "").lower()
    place = str(properties.get("type") or "").lower()
    if osm_key == "place":
        if osm_value in {"city", "municipality"}:
            return "city"
        if osm_value in {"town", "village", "hamlet", "borough", "suburb", "quarter", "neighbourhood"}:
            return "town" if osm_value in {"town", "village", "municipality"} else "barangay"
    if osm_key in {"amenity", "shop", "tourism", "leisure", "historic"}:
        return "landmark"
    if osm_key in {"railway", "public_transport"} or osm_value in {"bus_station", "station", "terminal"}:
        return "terminal"
    if place in {"city", "town", "village"}:
        return "city" if place == "city" else "town"
    return "place"


def _place_sort_key(place: dict[str, Any]) -> tuple[int, str, str]:
    order = {
        "city": 0,
        "town": 1,
        "barangay": 2,
        "terminal": 3,
        "landmark": 4,
        "place": 5,
        "stop": 6,
        "route": 7,
    }
    return (order.get(place.get("kind", ""), 9), place.get("city", ""), place.get("name", ""))


def _clean_destination(value: str) -> str:
    value = re.sub(r"\b(this destination|my destination|destination|from here|right now|please|pls|po|lang|diri|dito|gikan diri)\b", " ", value)
    value = re.sub(r"\b(my current location is|current location is|from|gikan|origin is|starting from)\s+.+?\b(?:what|which|how|to reach|reach|going to)\b", " ", value)
    value = re.sub(r"\b(which|what|how)\s+.*$", " ", value)
    value = re.sub(r"^(reach|get to|go to|towards?|to)\s+", " ", value)
    value = _clean_place_phrase(value)
    return value.title() if value else ""


def _clean_place_phrase(value: str) -> str:
    value = re.sub(r"\b(is at|is|at|sa)\b", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" ?.,")
    return value


def _route_center(points: list[dict[str, Any]]) -> Optional[dict[str, float]]:
    valid = [point for point in points if _valid_coord(point)]
    if not valid:
        return None
    return {
        "latitude": sum(float(point["latitude"]) for point in valid) / len(valid),
        "longitude": sum(float(point["longitude"]) for point in valid) / len(valid),
    }


def _destination_mentions_route(destination: dict[str, Any], route_text: str) -> bool:
    terms = [destination.get("name", ""), *(destination.get("aliases") or [])]
    normalized_terms = [normalize_text(term) for term in terms if normalize_text(term)]
    if any(term and term in route_text for term in normalized_terms):
        return True
    ignored = {"cebu", "city", "philippines", "current", "location"}
    tokens = {
        token
        for term in normalized_terms
        for token in term.split()
        if len(token) >= 4 and token not in ignored
    }
    return any(token in route_text for token in tokens)


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
    elif language == "es":
        replacements = {
            "Best option": "Mejor opcion",
            "Route": "Ruta",
            "Vehicle": "Vehiculo",
            "Board near": "Sube cerca de",
            "and alight near": "y baja cerca de",
            "Estimated fare": "Tarifa estimada",
            "Please tell me your destination so I can search every route.": "Dime tu destino para buscar todas las rutas.",
        }
    elif language == "ja":
        replacements = {
            "Best option": "Best option",
            "Route": "Route",
            "Vehicle": "Vehicle",
            "Estimated fare": "Estimated fare",
        }
    else:
        replacements = {}
    translated = english
    for source, target in replacements.items():
        translated = translated.replace(source, target)
    return translated
