# LoadSense

Integrated AI occupancy and transit intelligence for PUVs, based on the USJR FlowerBoys ASEAN Smart Cities roadmap.

LoadSense is implemented here as a software-only demo: edge hardware is simulated, the backend is FastAPI, model artifacts are local, and the commuter/operator UI is a lightweight browser app.

## What Is Implemented

- Mock GPS and occupancy telemetry for jeepney/PUV routes.
- Occupancy tier logic: Green, Yellow, Red, and Blinking Red.
- Stateful FastAPI backend with live fleet state, route deviation checks, ETA, demand forecast, operator alerts, and a context-based boarding assistant.
- Software-only edge line-crossing counter that exports frame counts and LED tiers.
- Responsive commuter app and operator dashboard served from the backend.
- Synthetic historical occupancy logs and checked-in model artifacts.

## Project Layout

```text
app/                 Browser UI for commuter and operator demo
backend/             FastAPI app, route intelligence, fleet state, API routes
cloud/               ETA and demand forecast training scripts/artifacts
data/                Synthetic history and generated edge counter outputs
docs/                Phase runbooks and implementation notes
edge/                Mock telemetry and line-crossing edge simulation
tests/               Lightweight health check
```

## Run The Demo

Start the backend:

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open the app:

```text
http://localhost:8000
```

Click `Seed Demo Data` in the UI, or send live mock telemetry:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

Generate edge line-crossing demo evidence:

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240
```

## API Highlights

- `POST /api/telemetry` accepts mock GPS and occupancy payloads.
- `GET /api/fleet` returns the live fleet state and summary metrics.
- `GET /api/alerts` returns operator-first anomaly alerts.
- `GET /api/eta/{stop_id}` returns ETA from the trained model when available.
- `GET /api/demand` returns demand forecast rows for the dashboard.
- `POST /api/chatbot` returns a boarding recommendation using live fleet context.
- `GET /api/routes` returns route polylines and stop metadata.

## Verification

```powershell
venv\Scripts\python.exe tests\run_health_check.py
venv\Scripts\python.exe tests\run_api_smoke.py
```

The API smoke check uses FastAPI `TestClient` across telemetry, fleet, alerts, demand, and chatbot endpoints.

## Documentation

Start with [docs/README.md](docs/README.md), then follow the phase files for setup, backend, edge simulation, frontend, and integration.
