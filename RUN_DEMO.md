# LoadSense Demo Runbook

This runbook describes the current software-only LoadSense prototype. The demo uses synthetic GPS and occupancy telemetry, local SQLite persistence, and browser-based commuter/operator screens.

## 1. Start The Backend

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

The FastAPI app starts the synthetic Cebu PUV fleet automatically during startup. No physical GPS unit, camera, LED strip, or external API key is required for the main demo.

## 2. Open The Demo Screens

- Landing/demo shell: `http://localhost:8000`
- Commuter app: `http://localhost:8000/mobile.html`
- Operator console: `http://localhost:8000/operator.html`
- Health endpoint: `http://localhost:8000/health`

## 3. What To Show

- The mobile map draws selected Cebu routes and moving synthetic PUV markers.
- Vehicle cards show ETA, occupancy count, occupancy tier, stop index, and route state.
- The boarding assistant answers route and crowding questions using live fleet context.
- The operator console shows fleet summary, demand forecast, alerts, incident history, and verification controls.
- Alerts are operator-first: they can be acknowledged, verified, marked as false alarms, or escalated.

## 4. Optional Extra Telemetry

Send an additional mock telemetry stream:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

WebSocket mode is also supported:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/api/ws/telemetry --interval 1
```

## 5. Generate Edge Counting Evidence

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240
```

This writes frame-level count and occupancy-tier evidence to `data/edge_line_crossing_counts.csv`. It simulates the downstream contract of the planned camera edge counter; it does not run real YOLO inference in this repo.

## 6. API Checks

```powershell
venv\Scripts\python.exe tests\run_health_check.py
venv\Scripts\python.exe tests\run_api_smoke.py
venv\Scripts\python.exe tests\run_chatbot_regression.py
venv\Scripts\python.exe tests\run_demo_state_check.py
```

The smoke checks cover telemetry, route listing/import, fleet state, alerts, incidents, database status, ETA, demand, and chatbot/suggestion behavior.

## 7. Docker Option

```powershell
docker compose up --build
```

The Docker service runs the same FastAPI app and static browser UI.

## 8. Demo Boundaries

- GPS movement is synthetic and route-aware.
- Passenger counts and historical demand are synthetic.
- The edge counter is a software simulation.
- The chatbot is deterministic and context-based for demo reliability.
- Live weather API calls and external LLM calls are not required.
- Real field accuracy, camera performance, and deployment safety still require pilot validation.
