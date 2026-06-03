# LoadSense Task Separation

This prototype is intentionally split into independently demoable layers.

## Edge Counting Demo

Purpose: prove the vehicle-side occupancy contract.

Files:

- `edge/line_crossing_counter.py`
- `data/edge_line_crossing_counts.csv`

Run:

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240 --output data\edge_line_crossing_counts.csv
```

Shows:

- bidirectional line crossing
- running passenger count
- occupancy tier
- simulated density zone
- LED state contract

## Interface Demo

Purpose: prove the commuter and operator product surfaces.

Files:

- `app/index.html`
- `app/mobile.html`
- `app/operator.html`
- `app/demo.js`
- `app/styles.css`

Run:

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000/mobile.html
http://localhost:8000/operator.html
```

Shows:

- mobile login
- commuter home
- mobile map
- route list
- chatbot tab
- operator fleet console
- demand forecast
- operator-first safety verification
- database status and incident logs

## Backend And Database Demo

Purpose: prove telemetry processing, persistence, and cloud logic.

Files:

- `backend/app/api/routes.py`
- `backend/app/core/state.py`
- `backend/app/db/sqlite_store.py`
- `data/loadsense_demo.sqlite`

Endpoints:

- `POST /api/telemetry`
- `GET /api/fleet`
- `GET /api/alerts`
- `POST /api/alerts/{alert_id}/ack`
- `GET /api/incidents`
- `GET /api/database/status`
- `POST /api/chatbot`
- `GET /api/routes`
- `GET /api/demand`

Boundary rule: the edge counter should not be embedded inside the browser UI. It is a separate vehicle-side process in the architecture diagram.
