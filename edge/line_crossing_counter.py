import argparse
import csv
import random
import sys
from datetime import datetime, UTC
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.core.config import config_value
from backend.app.core.occupancy import DEFAULT_CAPACITY, get_occupancy_tier


def simulated_tracks(frames: int, line_y: int) -> list[dict]:
    rows = []
    occupancy = 0
    previous_y = line_y + 30
    for frame in range(frames):
        movement = random.choice([-18, -10, -6, 8, 14])
        current_y = previous_y + movement
        direction = ""
        if previous_y > line_y >= current_y:
            occupancy += 1
            direction = "boarding"
        elif previous_y < line_y <= current_y:
            occupancy = max(0, occupancy - 1)
            direction = "alighting"
        occupancy = min(DEFAULT_CAPACITY + int(config_value("occupancy", "overload_demo_buffer", default=4)), occupancy)
        rows.append(
            {
                "timestamp": datetime.now(UTC).isoformat(),
                "frame": frame,
                "person_id": 1,
                "line_y": line_y,
                "centroid_y": current_y,
                "direction": direction,
                "running_count": occupancy,
                "tier": get_occupancy_tier(occupancy, DEFAULT_CAPACITY),
            }
        )
        previous_y = current_y
        if current_y < line_y - 80 or current_y > line_y + 80:
            previous_y = line_y + random.choice([-40, 40])
    return rows


def write_rows(rows: list[dict], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["timestamp", "frame", "person_id", "line_y", "centroid_y", "direction", "running_count", "tier"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Software-only bidirectional line-crossing passenger counter demo"
    )
    parser.add_argument("--frames", type=int, default=int(config_value("edge_counter", "frames", default=240)))
    parser.add_argument("--line-y", type=int, default=int(config_value("edge_counter", "line_y", default=240)))
    parser.add_argument("--output", default=config_value("data", "edge_counter_output", default=str(Path("data") / "edge_line_crossing_counts.csv")))
    args = parser.parse_args()

    rows = simulated_tracks(args.frames, args.line_y)
    write_rows(rows, Path(args.output))
    changes = [row for row in rows if row["direction"]]
    print(f"wrote {len(rows)} frame rows to {args.output}")
    print(f"detected crossings: {len(changes)}")
    print(f"final occupancy: {rows[-1]['running_count']} ({rows[-1]['tier']})")


if __name__ == "__main__":
    main()
