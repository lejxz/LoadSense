import math
from datetime import datetime


def haversine_m(lat1, lon1, lat2, lon2):
    radius = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def predict_eta(distance_to_stop_m, speed_kph, passenger_count, weather_score=0.86):
    hour = datetime.now().hour
    traffic = 1.25 if 7 <= hour <= 9 or 16 <= hour <= 19 else 1.0
    load_penalty = 1 + passenger_count / 60
    weather_penalty = 1 + (1 - weather_score) * 0.25
    speed_mps = max(speed_kph, 5) * 1000 / 3600
    eta = max(30, distance_to_stop_m / speed_mps * traffic * load_penalty * weather_penalty)
    return {"eta_seconds": round(eta), "confidence_lower": round(eta * 0.85), "confidence_upper": round(eta * 1.15)}
