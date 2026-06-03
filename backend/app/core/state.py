from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.core.compat import model_to_dict
from backend.app.core.occupancy import DEFAULT_CAPACITY, get_occupancy_tier
from backend.app.core.phase2 import predict_eta_details
from backend.app.core.route_deviation import detect_route_deviation
from backend.app.core.routes import nearest_stop_id
from backend.app.db.models import OperatorAlert, VehicleState


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return datetime.now(UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


class FleetStore:
    def __init__(self) -> None:
        self._vehicles: Dict[str, VehicleState] = {}
        self._alerts: List[OperatorAlert] = []

    def upsert_telemetry(self, payload: Any) -> VehicleState:
        tier = get_occupancy_tier(payload.occupancy, DEFAULT_CAPACITY)
        deviation = detect_route_deviation(payload.latitude, payload.longitude, payload.route)
        stop_id = nearest_stop_id(payload.route, payload.latitude, payload.longitude)
        time_of_day = parse_timestamp(payload.timestamp).hour
        traffic_factor = self._traffic_factor_from_tier(tier)
        eta = predict_eta_details(
            stop_id=stop_id,
            time_of_day=float(time_of_day),
            traffic_factor=traffic_factor,
            route=payload.route,
        )
        signal_quality = self._signal_quality(payload)

        state = VehicleState(
            vehicle_id=payload.vehicle_id,
            route=payload.route,
            latitude=payload.latitude,
            longitude=payload.longitude,
            occupancy=payload.occupancy,
            capacity=DEFAULT_CAPACITY,
            tier=tier,
            timestamp=payload.timestamp,
            eta_minutes=eta["eta_minutes"],
            eta_source=eta["source"],
            next_stop_id=stop_id,
            route_deviation=deviation,
            signal_quality=signal_quality,
            speed_kph=getattr(payload, "speed_kph", None),
            heading=getattr(payload, "heading", None),
        )
        self._vehicles[state.vehicle_id] = state
        self._raise_alerts(state)
        return state

    def fleet(self) -> List[VehicleState]:
        return sorted(self._vehicles.values(), key=lambda item: (item.route, item.vehicle_id))

    def alerts(self, include_acknowledged: bool = False) -> List[OperatorAlert]:
        alerts = self._alerts if include_acknowledged else [a for a in self._alerts if not a.acknowledged]
        return sorted(alerts, key=lambda item: item.timestamp, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> Optional[OperatorAlert]:
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return alert
        return None

    def recommendation(self, route: str, query: str = "") -> Dict[str, Any]:
        route_vehicles = [vehicle for vehicle in self.fleet() if vehicle.route == route]
        if not route_vehicles:
            return {
                "route": route,
                "answer": f"No live vehicles are reporting for Route {route} yet. Wait for the next telemetry update.",
                "context": [],
            }

        ranked = sorted(route_vehicles, key=lambda vehicle: (self._tier_penalty(vehicle.tier), vehicle.eta_minutes))
        best = ranked[0]
        action = "board" if best.tier in {"green", "yellow"} else "wait"
        answer = (
            f"For Route {route}, {action} Vehicle {best.vehicle_id}. "
            f"It is {best.tier.replace('_', ' ')} with {best.occupancy}/{best.capacity} passengers "
            f"and an ETA of {best.eta_minutes:.1f} minutes."
        )
        if best.route_deviation["anomaly"]:
            answer += " Operator verification is needed because the vehicle is off-route."
        if "least" in query.lower() or "crowd" in query.lower():
            answer += " This is currently the least crowded option in the live fleet."

        return {
            "route": route,
            "answer": answer,
            "context": [model_to_dict(vehicle) for vehicle in ranked],
        }

    def summary(self) -> Dict[str, Any]:
        vehicles = self.fleet()
        return {
            "vehicle_count": len(vehicles),
            "active_alerts": len(self.alerts()),
            "overloaded": sum(1 for vehicle in vehicles if vehicle.tier == "blinking_red"),
            "average_occupancy": round(
                sum(vehicle.occupancy for vehicle in vehicles) / len(vehicles),
                2,
            )
            if vehicles
            else 0.0,
        }

    def _raise_alerts(self, state: VehicleState) -> None:
        if state.tier == "blinking_red":
            self._append_alert(
                "high",
                state,
                f"{state.vehicle_id} is overloaded at {state.occupancy}/{state.capacity} passengers.",
            )
        if state.route_deviation["anomaly"]:
            self._append_alert(
                "high",
                state,
                f"{state.vehicle_id} deviated {state.route_deviation['deviation_meters']}m from Route {state.route}.",
            )
        if state.signal_quality != "ok":
            self._append_alert(
                "medium",
                state,
                f"{state.vehicle_id} reports {state.signal_quality.replace('_', ' ')} signal quality.",
            )

    def _append_alert(self, severity: str, state: VehicleState, message: str) -> None:
        duplicate = next((alert for alert in self._alerts[:8] if alert.vehicle_id == state.vehicle_id and alert.message == message), None)
        if duplicate:
            return
        self._alerts.append(
            OperatorAlert(
                id=str(uuid4()),
                severity=severity,
                vehicle_id=state.vehicle_id,
                route=state.route,
                message=message,
                timestamp=datetime.now(UTC).isoformat(),
            )
        )
        self._alerts = self._alerts[-100:]

    @staticmethod
    def _traffic_factor_from_tier(tier: str) -> float:
        return {
            "green": 0.9,
            "yellow": 1.05,
            "red": 1.2,
            "blinking_red": 1.35,
        }[tier]

    @staticmethod
    def _signal_quality(payload: Any) -> str:
        quality = getattr(payload, "signal_quality", None)
        if quality:
            return quality
        if getattr(payload, "latitude", 0.0) == 0.0 and getattr(payload, "longitude", 0.0) == 0.0:
            return "gps_dropout"
        return "ok"

    @staticmethod
    def _tier_penalty(tier: str) -> int:
        return {
            "green": 0,
            "yellow": 1,
            "red": 2,
            "blinking_red": 3,
        }[tier]


fleet_store = FleetStore()
