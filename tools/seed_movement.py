import time
import requests

API = 'http://127.0.0.1:8000/api/telemetry'

# simulate a vehicle moving along 04L polyline points
points = [
    (14.5992, 120.9840),
    (14.5995, 120.9844),
    (14.5998, 120.9847),
    (14.6001, 120.9850),
    (14.6005, 120.9856),
]

vehicle_id = 'J-SEED'
route = '04L'
for i, (lat, lon) in enumerate(points):
    payload = {
        'vehicle_id': vehicle_id,
        'route': route,
        'latitude': lat,
        'longitude': lon,
        'occupancy': max(1, (i*3) % 16),
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
        'speed_kph': 20,
        'signal_quality': 'ok'
    }
    try:
        r = requests.post(API, json=payload, timeout=5)
        print(r.status_code, r.text)
    except Exception as e:
        print('error', e)
    time.sleep(1)
