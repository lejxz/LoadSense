# Phase 4: Frontend Prototype

Status: complete for software-only demo

## What Phase 4 Adds

- A responsive browser app in `app/index.html`.
- Commuter route view with vehicle pins, nearest vehicle summary, and LED strip visual.
- Operator dashboard with fleet summary, vehicle list, demand forecast bars, and anomaly alerts.
- Boarding assistant that calls `POST /api/chatbot` with live fleet context.

## Run It

Start FastAPI:

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
```

Use `Seed Demo Data` to populate the dashboard immediately, or run `edge/mock_telemetry.py` for live updates.

## Design Notes

- The UI is plain HTML/CSS/JavaScript to avoid a package install during the hackathon sprint.
- The route map is a low-bandwidth schematic, matching the roadmap constraint that low-RAM Android devices should not depend on heavy live map rendering.
- The LED strip visual uses the same backend tier names as the edge and telemetry layers.
