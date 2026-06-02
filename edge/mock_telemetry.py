import sys
import time
import json
import random
import argparse
from datetime import datetime

ROUTE_POINTS = {
    "04L": (14.5992, 120.9840),
    "08A": (14.5988, 120.9835),
    "12B": (14.5990, 120.9844),
    "17C": (14.5986, 120.9838),
}


try:
    import websockets
except Exception:
    websockets = None


def make_payload(vehicle_id, route, base_lat, base_lon, occupancy):
    return {
        "vehicle_id": vehicle_id,
        "route": route,
        "latitude": base_lat + random.uniform(-0.0005, 0.0005),
        "longitude": base_lon + random.uniform(-0.0005, 0.0005),
        "occupancy": occupancy,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def get_base_coordinates(route):
    return ROUTE_POINTS.get(route, (14.5995, 120.9842))


def run_stdout(args):
    vehicle_id = args.vehicle_id
    route = args.route
    base_lat, base_lon = get_base_coordinates(route)
    occupancy = args.start
    while True:
        occupancy = max(0, occupancy + random.randint(-2, 3))
        occupancy = min(args.max, occupancy)
        payload = make_payload(vehicle_id, route, base_lat, base_lon, occupancy)
        print(json.dumps(payload), flush=True)
        time.sleep(args.interval)


def run_http(args):
    import urllib.request

    vehicle_id = args.vehicle_id
    route = args.route
    base_lat, base_lon = get_base_coordinates(route)
    occupancy = args.start
    url = args.url
    while True:
        occupancy = max(0, occupancy + random.randint(-2, 3))
        occupancy = min(args.max, occupancy)
        payload = make_payload(vehicle_id, route, base_lat, base_lon, occupancy)
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                print("posted", payload["vehicle_id"], "status", resp.status)
        except Exception as e:
            print("http send error:", e, file=sys.stderr)
        time.sleep(args.interval)


async def run_ws_async(args):
    if websockets is None:
        print("websockets package not available", file=sys.stderr)
        return
    vehicle_id = args.vehicle_id
    route = args.route
    base_lat, base_lon = get_base_coordinates(route)
    occupancy = args.start
    url = args.url
    async with websockets.connect(url) as ws:
        while True:
            occupancy = max(0, occupancy + random.randint(-2, 3))
            occupancy = min(args.max, occupancy)
            payload = make_payload(vehicle_id, route, base_lat, base_lon, occupancy)
            text = json.dumps(payload)
            await ws.send(text)
            try:
                resp = await ws.recv()
                print("ws ack:", resp)
            except Exception:
                pass
            await asyncio.sleep(args.interval)


def run_ws(args):
    import asyncio

    asyncio.run(run_ws_async(args))


def parse_args():
    p = argparse.ArgumentParser(description="Mock telemetry generator")
    p.add_argument("--mode", choices=["stdout", "http", "ws"], default="stdout")
    p.add_argument("--url", default="ws://localhost:8000/ws/telemetry")
    p.add_argument("--vehicle-id", default="J-001")
    p.add_argument("--route", default="04L")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--max", type=int, default=16)
    p.add_argument("--interval", type=float, default=1.0)
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.mode == "stdout":
        run_stdout(args)
    elif args.mode == "http":
        run_http(args)
    elif args.mode == "ws":
        run_ws(args)

