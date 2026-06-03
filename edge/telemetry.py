import httpx


async def post_telemetry(payload, backend_url="http://127.0.0.1:8000"):
    async with httpx.AsyncClient(timeout=4.0) as client:
        try:
            response = await client.post(f"{backend_url}/api/telemetry", json=payload)
            response.raise_for_status()
            return True
        except Exception as exc:
            print(f"[telemetry] POST failed for {payload['vehicle_id']}: {exc}")
            return False
