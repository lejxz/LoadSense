import argparse
import csv
import os
import random
from datetime import datetime, timedelta


ROUTES = ["04L", "08A", "12B", "17C"]


def generate_rows(rows: int):
    start = datetime(2026, 1, 1, 6, 0, 0)
    for index in range(rows):
        timestamp = start + timedelta(minutes=15 * index)
        route = ROUTES[index % len(ROUTES)]
        stop_index = index % 12
        time_of_day = timestamp.hour + timestamp.minute / 60.0
        traffic_factor = round(random.uniform(0.6, 1.6), 2)
        base_demand = 4 + (stop_index % 5)
        count = max(0, min(20, int(round(base_demand * traffic_factor + random.randint(0, 6)))))
        yield {
            "timestamp": timestamp.isoformat(),
            "route": route,
            "stop_index": stop_index,
            "time_of_day": round(time_of_day, 2),
            "traffic_factor": traffic_factor,
            "count": count,
        }


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic occupancy history CSV")
    parser.add_argument("--rows", type=int, default=500)
    parser.add_argument("--output", default=os.path.join("data", "synthetic_occupancy_logs.csv"))
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "route", "stop_index", "time_of_day", "traffic_factor", "count"],
        )
        writer.writeheader()
        for row in generate_rows(args.rows):
            writer.writerow(row)

    print(f"wrote {args.rows} rows to {args.output}")


if __name__ == "__main__":
    main()
