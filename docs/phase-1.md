# Phase 1: Foundation

Status: in progress

## What Exists Now

- `requirements.txt` with the project dependencies
- `cloud/` as the placeholder for future backend/model work
- `backend/app/main.py` with a `/health` endpoint
- `backend/app/api/routes.py` with telemetry, ETA, demand, and WebSocket telemetry routes
- `backend/app/core/occupancy.py` with shared occupancy thresholds and tier logic
- `edge/mock_telemetry.py` with stdout, HTTP, and WebSocket mock telemetry modes
- `data/generate_synthetic_history.py` for producing synthetic occupancy logs
- `app/index.html` as a frontend placeholder

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
venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/ws/telemetry --interval 1
```

Send mock telemetry over HTTP:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry
```

## Next Phase 1 Items

- Add a persistent mock telemetry stream instead of printing only acknowledgements.
- Expand the synthetic CSV and keep a checked-in sample for model training.
- Keep the docs updated as the backend and edge scripts evolve.

## Synthetic Data

Generate or refresh the sample CSV with:

```powershell
venv\Scripts\python.exe data\generate_synthetic_history.py --rows 500
```

The output file is `data/synthetic_occupancy_logs.csv`.
