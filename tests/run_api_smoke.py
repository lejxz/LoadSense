import os
import sys

from fastapi.testclient import TestClient

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backend.app.main import app


def main():
    client = TestClient(app)
    payload = {
        "vehicle_id": "J-214",
        "route": "04L",
        "latitude": 14.5992,
        "longitude": 120.9840,
        "occupancy": 9,
        "timestamp": "2026-06-03T02:30:00+00:00",
    }

    checks = [
        ("post", "/api/telemetry", payload),
        ("get", "/api/config", None),
        ("get", "/api/routes", None),
        ("get", "/api/fleet", None),
        ("get", "/api/alerts", None),
        ("get", "/api/demand", None),
        ("post", "/api/chatbot", {"route": "04L", "query": "Which jeepney is least crowded right now?"}),
    ]

    for method, path, body in checks:
        response = getattr(client, method)(path, json=body) if body else getattr(client, method)(path)
        print(path, response.status_code)
        if response.status_code != 200:
            raise SystemExit(response.text)

    print("api smoke ok")


if __name__ == "__main__":
    main()
