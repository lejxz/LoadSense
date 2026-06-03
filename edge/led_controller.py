import asyncio
import json
import threading

try:
    import websockets
except Exception:
    websockets = None

COLORS = {"GREEN": "\033[92m", "YELLOW": "\033[93m", "RED": "\033[91m", "BLINKING_RED": "\033[5;91m"}
RESET = "\033[0m"
clients = set()
loop = None


async def _handler(websocket):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.discard(websocket)


async def _server():
    async with websockets.serve(_handler, "127.0.0.1", 8765):
        await asyncio.Future()


def start_websocket_server():
    global loop
    if websockets is None or loop:
        return
    loop = asyncio.new_event_loop()
    threading.Thread(target=lambda: loop.run_until_complete(_server()), daemon=True).start()


async def _broadcast(payload):
    await asyncio.gather(*[client.send(json.dumps(payload)) for client in list(clients)], return_exceptions=True)


def update_led_state(vehicle_id, occupancy_tier, passenger_count):
    blocks = " ".join(["■"] * 12)
    print(f"{COLORS.get(occupancy_tier, '')}[LED {vehicle_id}] {occupancy_tier:<12} {blocks} {passenger_count}/16 passengers{RESET}")
    if loop:
        asyncio.run_coroutine_threadsafe(_broadcast({"vehicle_id": vehicle_id, "occupancy_tier": occupancy_tier, "passenger_count": passenger_count}), loop)
