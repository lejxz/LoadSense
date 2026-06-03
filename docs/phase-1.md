# Phase 1: Foundation

Status: complete

## What Exists Now

- `requirements.txt` with the project dependencies
- `cloud/` with training scripts and checked-in artifacts
- `backend/app/main.py` with a `/health` endpoint
- `backend/app/api/routes.py` with telemetry, ETA, demand, fleet, route, alert, chatbot, and WebSocket telemetry routes
- `backend/app/core/occupancy.py` with shared occupancy thresholds and tier logic
- `edge/mock_telemetry.py` with stdout, HTTP, and WebSocket mock telemetry modes
- `data/generate_synthetic_history.py` for producing synthetic occupancy logs
- `app/index.html` as the commuter/operator frontend

## Phase 1 Goal

Build the base data flow for the prototype:

1. Generate mock telemetry.
2. Send it to the backend.
3. Keep a simple, visible project structure for later ETA, demand, and dashboard work.

## Run It

Start the backend:

```powershell
$env:PYTHONPATH='.'; uvicorn backend.app.main:app --reload --app-dir backend
```

Send mock telemetry over WebSocket:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/api/ws/telemetry --interval 1
```

Send mock telemetry over HTTP:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry
```

## Synthetic Data

Generate or refresh the sample CSV with:

```powershell
venv\Scripts\python.exe data\generate_synthetic_history.py --rows 500
```

The output file is `data/synthetic_occupancy_logs.csv`.

The checked-in sample has 500 rows and is sufficient for the prototype model scripts.
