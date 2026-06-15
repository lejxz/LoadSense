import os
import json
from typing import Any, Dict, Optional, List
from datetime import UTC, datetime

# Attempt to import Google GenAI; if it fails, the module handles it gracefully.
try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from backend.app.core.compat import model_to_dict
from backend.app.core.routes import list_routes
from backend.app.db import sqlite_store


def get_llm_recommendation(
    fleet_store: Any,
    route: str,
    query: str,
    country: Optional[str] = None,
    origin_text: str = "",
    origin_latitude: Optional[float] = None,
    origin_longitude: Optional[float] = None,
    destination: str = "",
    destination_latitude: Optional[float] = None,
    destination_longitude: Optional[float] = None,
) -> Optional[Dict[str, Any]]:
    """
    Attempts to use an LLM (Gemini) to answer the user's query.
    Returns None if the LLM is not configured, allowing fallback to hardcoded heuristics.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or genai is None:
        return None  # Optional LLM not configured

    client = genai.Client(api_key=api_key)

    # Shared context to extract from function calls
    ui_context = []
    target_route = route

    def get_route_info(route_id: str) -> str:
        """Get details about a specific transit route."""
        nonlocal target_route
        route_info = next((item for item in list_routes() if item.get("route") == route_id and (not country or item.get("country") == country)), None)
        target_route = route_id
        return json.dumps(route_info) if route_info else "Route not found."

    def get_live_vehicles(route_id: str) -> str:
        """Get the list of live vehicles currently reporting on a specific route, including their occupancy and ETAs."""
        nonlocal ui_context, target_route
        vehicles = [
            v for v in fleet_store.fleet()
            if v.route == route_id and (not country or fleet_store._vehicle_country(v) == country)
        ]
        ui_context = [model_to_dict(v) for v in vehicles]
        target_route = route_id
        return json.dumps(ui_context) if ui_context else "No live vehicles reporting on this route."

    def find_routes_between(origin: str, destination: str) -> str:
        """Search for recommended routes and vehicles between an origin and a destination."""
        nonlocal ui_context
        orig = origin or origin_text
        dest = destination or destination_longitude
        sug = fleet_store.route_suggestions(
            query=f"from {orig} to {dest}",
            country=country,
            origin_text=orig,
            destination=dest,
            limit=5
        )
        ui_context = sug.get("suggestions", [])
        return json.dumps(sug)

    system_prompt = (
        "You are a helpful transit assistant for the LoadSense application. "
        "You help users find routes, check live Public Utility Vehicle (PUV) statuses, and avoid crowded vehicles. "
        f"Current Country Context: {country or 'Unknown'}. "
        f"Current Selected Route: {route or 'None'}. "
        "Use the provided tools to fetch real-time data before answering. "
        "Keep your answers concise and directly useful to a commuter."
    )

    try:
        chat = client.chats.create(
            model="gemini-2.5-flash-lite",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.0,
                tools=[get_route_info, get_live_vehicles, find_routes_between]
            )
        )
        response = chat.send_message(query)
        answer = response.text

        if answer is None:
            return None

        sqlite_store.save_chat_query(target_route or "all", query, answer, datetime.now(UTC).isoformat())

        return {
            "route": target_route or "",
            "answer": answer,
            "context": ui_context,
            "matches": [],
            "language": "en",
            "intent": "llm_response"
        }

    except Exception as e:
        print(f"LLM Chatbot error: {e}")
        return None  # Fallback to hardcoded logic on error
