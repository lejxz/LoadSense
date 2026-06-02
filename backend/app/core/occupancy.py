from dataclasses import dataclass


@dataclass(frozen=True)
class OccupancyThresholds:
    green_max: float = 0.50
    yellow_max: float = 0.75
    red_max: float = 1.00


DEFAULT_CAPACITY = 16
DEFAULT_THRESHOLDS = OccupancyThresholds()


def get_occupancy_tier(occupancy: int, capacity: int = DEFAULT_CAPACITY) -> str:
    if capacity <= 0:
        raise ValueError("capacity must be positive")

    ratio = occupancy / capacity
    if ratio <= DEFAULT_THRESHOLDS.green_max:
        return "green"
    if ratio <= DEFAULT_THRESHOLDS.yellow_max:
        return "yellow"
    if ratio <= DEFAULT_THRESHOLDS.red_max:
        return "red"
    return "blinking_red"
