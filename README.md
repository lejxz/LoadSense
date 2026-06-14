# LoadSense

Integrated AI occupancy and transit intelligence for PUVs, based on the USJR FlowerBoys ASEAN Smart Cities roadmap.

LoadSense is implemented here as a software-only demo: edge hardware is simulated, the backend is FastAPI with SQLite persistence, model artifacts are local, and the commuter/operator UI is a lightweight browser app.

## What Is Implemented

- Automatic synthetic GPS and occupancy telemetry for Cebu jeepney/PUV routes.
- Occupancy tier logic: Green, Yellow, Red, and Blinking Red.
- Stateful FastAPI backend with SQLite persistence, live fleet state, route deviation checks, driving anomaly alerts, ETA, demand forecast, operator alerts, and a context-based boarding assistant.
- Software-only edge line-crossing counter that exports frame counts and LED tiers.
- Separated commuter mobile app and operator console served from the backend.
- Synthetic historical occupancy logs and checked-in model artifacts.

## Project Layout

```text
app/                 Browser UI for commuter and operator demo
backend/             FastAPI app, route intelligence, fleet state, API routes
cloud/               ETA and demand forecast training scripts/artifacts
data/                Synthetic history, SQLite database, and generated edge counter outputs
docs/                Phase runbooks and implementation notes
edge/                Mock telemetry and line-crossing edge simulation
tests/               Lightweight health check
```

## Run The Demo

Start the backend:

```powershell
(for dev)
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload

(for demo)
$env:PYTHONPATH='.'; .\venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open the app:

```text
http://localhost:8000
```

Direct demo pages:

```text
http://localhost:8000/mobile.html
http://localhost:8000/operator.html
```

The interface demo starts with looping synthetic PUVs automatically when the backend starts. Each Cebu route gets multiple simulated PUVs that move along the route polyline and persist through SQLite.

Optional: send an extra mock edge telemetry stream:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

Docker Compose:

```powershell
docker compose up --build
```

Generate edge line-crossing demo evidence:

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240
```

The line-crossing counter should stay separate for the hackathon demo. It represents the vehicle-side camera and edge inference program, while the web app shows the downstream commuter and operator experiences that consume occupancy telemetry.

## API Highlights

- `POST /api/telemetry` accepts mock GPS and occupancy payloads.
- `GET /api/fleet` returns the live fleet state and summary metrics.
- `GET /api/alerts` returns operator-first anomaly alerts.
- `GET /api/incidents` returns persisted historical safety incidents.
- `GET /api/database/status` returns SQLite table counts.
- `GET /api/eta/{stop_id}` returns ETA from the trained model when available.
- `GET /api/demand` returns demand forecast rows for the dashboard.
- `POST /api/chatbot` returns a boarding recommendation using live fleet context.
- `GET /api/routes` returns SQLite-backed Cebu route polylines and stop metadata. Use `?route=04L` or `?q=Parkmall` to filter.

## Verification

```powershell
venv\Scripts\python.exe tests\run_health_check.py
venv\Scripts\python.exe tests\run_api_smoke.py
```

The API smoke check uses FastAPI `TestClient` across telemetry, fleet, alerts, demand, and chatbot endpoints.

## Documentation

Start with [RUN_DEMO.md](RUN_DEMO.md) for the live demo script, [docs/REQUIREMENTS_COVERAGE.md](docs/REQUIREMENTS_COVERAGE.md) for implementation status, and [docs/DATA_SOURCES_AND_APIS.md](docs/DATA_SOURCES_AND_APIS.md) for dataset/API citations and license links.
