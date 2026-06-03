import argparse
import asyncio
import math
import random
from datetime import datetime, timezone

from led_controller import start_websocket_server, update_led_state
from telemetry import post_telemetry

ROUTE_ID = "ayala-sm-carbon"
WAYPOINTS = [(10.3181, 123.9052), (10.3157, 123.9004), (10.3112, 123.9187), (10.3056, 123.9141), (10.2947, 123.9018), (10.3036, 123.8951), (10.3181, 123.9052)]


def occupancy_tier(count):
    if count <= 5:
        return "GREEN"
    if count <= 10:
        return "YELLOW"
    if count <= 15:
        return "RED"
    return "BLINKING_RED"


def heading_between(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    dlon = lon2 - lon1
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(y, x)) + 360) % 360


class Vehicle:
    def __init__(self, index, force_deviation=False):
        self.vehicle_id = f"JY-{index + 1:03d}"
        self.position_index = index % len(WAYPOINTS)
        self.passenger_count = random.randint(2, 9)
        self.force_deviation = force_deviation and index == 0

    def step(self):
        self.passenger_count = max(0, min(17, self.passenger_count + random.choice([-2, -1, 0, 1, 2])))
        self.position_index = (self.position_index + 1) % len(WAYPOINTS)
        lat, lon = WAYPOINTS[self.position_index]
        if self.force_deviation:
            lat += 0.006
            lon += 0.006
        next_point = WAYPOINTS[(self.position_index + 1) % len(WAYPOINTS)]
        return {
            "vehicle_id": self.vehicle_id,
            "route_id": ROUTE_ID,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "passenger_count": self.passenger_count,
            "occupancy_tier": occupancy_tier(self.passenger_count),
            "lat": lat,
            "lon": lon,
            "speed_kph": round(random.uniform(14, 32), 1),
            "heading_deg": round(heading_between((lat, lon), next_point)),
        }


async def run_simulator(vehicle_count, backend_url, force_deviation):
    random.seed(42)
    start_websocket_server()
    vehicles = [Vehicle(i, force_deviation) for i in range(vehicle_count)]
    print(f"LoadSense edge simulator running with {vehicle_count} vehicle(s). Ctrl+C to stop.")
    while True:
        for vehicle in vehicles:
            payload = vehicle.step()
            update_led_state(payload["vehicle_id"], payload["occupancy_tier"], payload["passenger_count"])
            await post_telemetry(payload, backend_url)
        await asyncio.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Simulated LoadSense edge device")
    parser.add_argument("--vehicles", type=int, default=1)
    parser.add_argument("--backend-url", default="http://127.0.0.1:8000")
    parser.add_argument("--force-deviation", action="store_true")
    args = parser.parse_args()
    asyncio.run(run_simulator(args.vehicles, args.backend_url, args.force_deviation))


if __name__ == "__main__":
    main()
