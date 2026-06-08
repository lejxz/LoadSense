from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from backend.app.core.compat import model_to_dict
from backend.app.core.config import config_value
from backend.app.core.occupancy import DEFAULT_CAPACITY, get_occupancy_tier
from backend.app.core.phase2 import predict_eta_details
from backend.app.core.route_deviation import detect_route_deviation
from backend.app.core.routes import list_routes, nearest_stop_id
from backend.app.core.transit import find_transit_suggestions
from backend.app.db import sqlite_store
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
        sqlite_store.init_db()
        self._vehicles: Dict[str, VehicleState] = {
            vehicle.vehicle_id: vehicle for vehicle in sqlite_store.load_vehicle_states()
        }
        self._alerts: List[OperatorAlert] = sqlite_store.load_alerts()

    def upsert_telemetry(self, payload: Any) -> VehicleState:
        previous = self._vehicles.get(payload.vehicle_id)
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
            direction=getattr(payload, "direction", None),
            status=getattr(payload, "status", "active"),
        )
        self._vehicles[state.vehicle_id] = state
        received_at = datetime.now(UTC).isoformat()
        sqlite_store.save_vehicle_state(state, received_at=received_at)
        self._raise_alerts(state, previous)
        return state

    def fleet(self) -> List[VehicleState]:
        return sorted(self._vehicles.values(), key=lambda item: (item.route, item.vehicle_id))

    def alerts(self, include_acknowledged: bool = False) -> List[OperatorAlert]:
        alerts = self._alerts if include_acknowledged else [a for a in self._alerts if not a.acknowledged]
        return sorted(alerts, key=lambda item: item.timestamp, reverse=True)

    def acknowledge_alert(self, alert_id: str) -> Optional[OperatorAlert]:
        return self.verify_alert(alert_id, action="verified", note="")

    def verify_alert(self, alert_id: str, action: str = "verified", note: str = "") -> Optional[OperatorAlert]:
        for alert in self._alerts:
            if alert.id == alert_id:
                verified_at = datetime.now(UTC).isoformat()
                updated = sqlite_store.verify_alert(alert_id, action, note, verified_at)
                if updated is None:
                    return None
                alert.acknowledged = updated.acknowledged
                alert.verification_status = updated.verification_status
                alert.resolution_note = updated.resolution_note
                alert.verified_at = updated.verified_at
                return alert
        return None

    def route_suggestions(
        self,
        query: str = "",
        route: str = "",
        origin_text: str = "",
        origin_latitude: Optional[float] = None,
        origin_longitude: Optional[float] = None,
        destination: str = "",
        destination_latitude: Optional[float] = None,
        destination_longitude: Optional[float] = None,
        limit: int = 5,
    ) -> Dict[str, Any]:
        return find_transit_suggestions(
            routes=list_routes(),
            vehicles=[model_to_dict(vehicle) for vehicle in self.fleet()],
            query=query,
            selected_route=route,
            origin_text=origin_text,
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            destination_text=destination,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
            limit=limit,
        )

    def recommendation(
        self,
        route: str,
        query: str = "",
        origin_text: str = "",
        origin_latitude: Optional[float] = None,
        origin_longitude: Optional[float] = None,
        destination: str = "",
        destination_latitude: Optional[float] = None,
        destination_longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        if self._is_greeting_or_smalltalk(query):
            answer = "Hello. Tell me your current location and destination, and I can recommend the best route and PUV."
            sqlite_store.save_chat_query("chat", query, answer, datetime.now(UTC).isoformat())
            return {
                "route": route,
                "answer": answer,
                "context": [],
                "matches": [],
                "language": "en",
                "intent": "smalltalk",
            }

        explicit_route = self._route_from_query(query)
        context_route = explicit_route or (route if self._uses_route_context(query) else "")
        if self._is_route_info_query(query):
            answer, context = self._route_info_answer(context_route)
            sqlite_store.save_chat_query(context_route or "all", query, answer, datetime.now(UTC).isoformat())
            return {"route": context_route or "", "answer": answer, "context": context, "matches": [], "language": "en", "intent": "route_info"}

        if self._is_avoid_query(query):
            answer, context = self._avoidance_answer(context_route)
            saved_route = context_route or "all"
            sqlite_store.save_chat_query(saved_route, query, answer, datetime.now(UTC).isoformat())
            return {
                "route": saved_route,
                "answer": answer,
                "context": context,
                "matches": [],
                "language": "en",
                "intent": "avoid",
            }

        if self._is_least_crowded_query(query):
            answer, context = self._least_crowded_answer(context_route)
            sqlite_store.save_chat_query(context_route or "all", query, answer, datetime.now(UTC).isoformat())
            return {"route": context_route or "all", "answer": answer, "context": context, "matches": [], "language": "en", "intent": "least_crowded"}

        if self._is_boarding_followup(query) and context_route:
            answer, context = self._best_boarding_answer(context_route)
            sqlite_store.save_chat_query(context_route, query, answer, datetime.now(UTC).isoformat())
            return {"route": context_route, "answer": answer, "context": context, "matches": [], "language": "en", "intent": "boarding"}

        suggestion_result = self.route_suggestions(
            query=query,
            route=route,
            origin_text=origin_text,
            origin_latitude=origin_latitude,
            origin_longitude=origin_longitude,
            destination=destination,
            destination_latitude=destination_latitude,
            destination_longitude=destination_longitude,
        )
        if suggestion_result["destination"] or suggestion_result["suggestions"]:
            answer = suggestion_result["answer"]
            sqlite_store.save_chat_query(route, query, answer, datetime.now(UTC).isoformat())
            return {
                "route": route,
                "answer": answer,
                "context": suggestion_result["suggestions"],
                "origin": suggestion_result["origin"],
                "destination": suggestion_result["destination"],
                "matches": suggestion_result["matches"],
                "language": suggestion_result["language"],
                "intent": "trip_recommendation",
            }

        if not route:
            answer = suggestion_result["answer"]
            sqlite_store.save_chat_query("all", query, answer, datetime.now(UTC).isoformat())
            return {
                "route": "",
                "answer": answer,
                "context": [],
                "origin": suggestion_result["origin"],
                "destination": suggestion_result["destination"],
                "matches": [],
                "language": suggestion_result["language"],
            }

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

        sqlite_store.save_chat_query(route, query, answer, datetime.now(UTC).isoformat())
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

    def incidents(self, limit: int = 50) -> List[Dict[str, Any]]:
        return sqlite_store.list_incidents(limit=limit)

    def database_status(self) -> Dict[str, Any]:
        return sqlite_store.database_status()

    def _raise_alerts(self, state: VehicleState, previous: Optional[VehicleState] = None) -> None:
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
        if state.speed_kph is not None and state.speed_kph > float(config_value("safety", "speed_limit_kph", default=60)):
            self._append_alert(
                "medium",
                state,
                f"{state.vehicle_id} is overspeeding at {state.speed_kph:.1f} kph.",
            )
        if previous and previous.speed_kph is not None and state.speed_kph is not None:
            delta = previous.speed_kph - state.speed_kph
            if delta >= float(config_value("safety", "sudden_stop_delta_kph", default=25)):
                self._append_alert(
                    "medium",
                    state,
                    f"{state.vehicle_id} reports sudden deceleration of {delta:.1f} kph.",
                )

    def _append_alert(self, severity: str, state: VehicleState, message: str) -> None:
        duplicate = next((alert for alert in self._alerts if not alert.acknowledged and alert.vehicle_id == state.vehicle_id and alert.message == message), None)
        if duplicate:
            return
        alert = OperatorAlert(
            id=str(uuid4()),
            severity=severity,
            vehicle_id=state.vehicle_id,
            route=state.route,
            message=message,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._alerts.append(alert)
        sqlite_store.save_alert(alert)
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

    @staticmethod
    def _is_avoid_query(query: str) -> bool:
        text = query.lower()
        return any(word in text for word in ["avoid", "overloaded", "do not ride", "don't ride"])

    @staticmethod
    def _is_least_crowded_query(query: str) -> bool:
        text = query.lower()
        return "least crowded" in text or "less crowded" in text or "most seats" in text or "available seats" in text

    @staticmethod
    def _is_boarding_followup(query: str) -> bool:
        text = query.lower().strip(" ?.!")
        return text in {"which do i ride", "which should i ride", "what do i ride", "which jeepney do i ride", "which jeepney should i ride", "which puv do i ride"}

    @staticmethod
    def _is_route_info_query(query: str) -> bool:
        text = query.lower()
        return any(phrase in text for phrase in ["explain this route", "explain that route", "what is this route", "what is that route", "route details"])

    @staticmethod
    def _uses_route_context(query: str) -> bool:
        text = query.lower()
        return any(phrase in text for phrase in ["that route", "this route", "current route", "selected route", "in that route", "in this route"]) or FleetStore._is_boarding_followup(query)

    @staticmethod
    def _is_greeting_or_smalltalk(query: str) -> bool:
        text = query.strip().lower()
        normalized = "".join(ch for ch in text if ch.isalnum() or ch.isspace()).strip()
        greetings = {"hi", "hello", "hello?", "hey", "good morning", "good afternoon", "good evening", "thanks", "thank you"}
        return text in greetings or normalized in greetings

    def _route_from_query(self, query: str) -> str:
        text = query.lower()
        for route in list_routes():
            route_id = str(route.get("route", ""))
            if route_id and route_id.lower() in text:
                return route_id
        return ""

    def _avoidance_answer(self, route: str = "") -> tuple[str, List[Dict[str, Any]]]:
        route_vehicles = [vehicle for vehicle in self.fleet() if not route or vehicle.route == route]
        context = [model_to_dict(vehicle) for vehicle in route_vehicles]
        route_label = f"Route {route}" if route else "the live fleet"
        if not route_vehicles:
            return f"No live PUVs are reporting for {route_label} right now, so I cannot identify a vehicle to avoid yet.", context

        risky = [
            vehicle for vehicle in route_vehicles
            if vehicle.tier in {"red", "blinking_red"}
            or vehicle.route_deviation.get("anomaly")
            or vehicle.signal_quality != "ok"
        ]
        risky = sorted(risky, key=lambda vehicle: (self._tier_penalty(vehicle.tier), -vehicle.occupancy), reverse=True)
        better = sorted(
            [vehicle for vehicle in route_vehicles if vehicle not in risky],
            key=lambda vehicle: (self._tier_penalty(vehicle.tier), vehicle.eta_minutes),
        )
        if risky:
            avoid_list = ", ".join(
                f"{vehicle.vehicle_id} on Route {vehicle.route} ({vehicle.occupancy}/{vehicle.capacity}, {self._avoid_reason(vehicle)})"
                for vehicle in risky[:3]
            )
            if better:
                best = better[0]
                return (
                    f"For {route_label}, avoid {avoid_list}. Better option: {best.vehicle_id} on Route {best.route} "
                    f"has {best.occupancy}/{best.capacity} riders, {best.tier.replace('_', ' ')}, "
                    f"and ETA {best.eta_minutes:.1f} min.",
                    [model_to_dict(best), *[model_to_dict(vehicle) for vehicle in risky]],
                )
            return f"For {route_label}, avoid {avoid_list}. All reporting PUVs in this set look crowded or need verification.", context

        best = better[0]
        return (
            f"For {route_label}, no reporting PUV needs to be avoided right now. Best current option: "
            f"{best.vehicle_id} on Route {best.route} with {best.occupancy}/{best.capacity} riders, {best.tier.replace('_', ' ')}, "
            f"ETA {best.eta_minutes:.1f} min.",
            context,
        )

    def _least_crowded_answer(self, route: str = "") -> tuple[str, List[Dict[str, Any]]]:
        vehicles = [vehicle for vehicle in self.fleet() if (not route or vehicle.route == route) and vehicle.status != "idle"]
        context = [model_to_dict(vehicle) for vehicle in vehicles]
        route_label = f"Route {route}" if route else "the live fleet"
        if not vehicles:
            return f"No live PUVs are reporting for {route_label} right now.", context
        ranked = sorted(vehicles, key=lambda vehicle: (vehicle.occupancy / max(1, vehicle.capacity), self._tier_penalty(vehicle.tier), vehicle.eta_minutes))
        best = ranked[0]
        seats = max(0, best.capacity - best.occupancy)
        return (
            f"Least crowded option for {route_label}: {best.vehicle_id} on Route {best.route}. "
            f"It has {best.occupancy}/{best.capacity} riders ({seats} seats available), {best.tier.replace('_', ' ')}, "
            f"ETA {best.eta_minutes:.1f} min.",
            [model_to_dict(vehicle) for vehicle in ranked],
        )

    def _best_boarding_answer(self, route: str) -> tuple[str, List[Dict[str, Any]]]:
        vehicles = [vehicle for vehicle in self.fleet() if vehicle.route == route and vehicle.status != "idle"]
        context = [model_to_dict(vehicle) for vehicle in vehicles]
        if not vehicles:
            return f"No live PUVs are reporting for Route {route} right now.", context
        ranked = sorted(vehicles, key=lambda vehicle: (self._tier_penalty(vehicle.tier), vehicle.eta_minutes, vehicle.occupancy))
        best = ranked[0]
        return (
            f"Ride {best.vehicle_id} on Route {route}. It has {best.occupancy}/{best.capacity} riders, "
            f"{best.tier.replace('_', ' ')}, and ETA {best.eta_minutes:.1f} min.",
            [model_to_dict(vehicle) for vehicle in ranked],
        )

    def _route_info_answer(self, route: str) -> tuple[str, List[Dict[str, Any]]]:
        if not route:
            return "Which route do you want me to explain? Ask after a recommendation or include the route code.", []
        route_info = next((item for item in list_routes() if item.get("route") == route), None)
        vehicles = [vehicle for vehicle in self.fleet() if vehicle.route == route]
        context = [model_to_dict(vehicle) for vehicle in vehicles]
        if not route_info:
            return f"I do not have route details for Route {route} yet.", context
        endpoints = route_info.get("endpoints") or []
        landmarks = route_info.get("landmarks") or []
        live = f"{len(vehicles)} live PUVs" if vehicles else "no live PUVs reporting"
        return (
            f"Route {route}: {route_info.get('name', route)}. "
            f"Area: {route_info.get('city') or route_info.get('zone') or 'unknown'}. "
            f"Endpoints: {', '.join(endpoints[:2]) if endpoints else 'not listed'}. "
            f"Key stops: {', '.join(landmarks[:5]) if landmarks else 'not listed'}. "
            f"Current status: {live}.",
            context,
        )

    @staticmethod
    def _avoid_reason(vehicle: VehicleState) -> str:
        if vehicle.route_deviation.get("anomaly"):
            return "off route"
        if vehicle.signal_quality != "ok":
            return vehicle.signal_quality.replace("_", " ")
        return vehicle.tier.replace("_", " ")


fleet_store = FleetStore()
