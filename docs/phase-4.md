# Phase 4: Frontend Prototype

Status: complete for software-only demo

## What Phase 4 Adds

- A role launcher in `app/index.html`.
- A phone-shaped commuter app in `app/mobile.html` with login, home, map, route list, and chatbot tabs.
- A separated operator console in `app/operator.html` with fleet summary, vehicle list, demand forecast bars, anomaly alerts, and alert verification.
- Boarding assistant that calls `POST /api/chatbot` with live fleet context.

## Run It

Start FastAPI:

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Open:

```text
http://localhost:8000
http://localhost:8000/mobile.html
http://localhost:8000/operator.html
```

Use the commuter `+` button or operator `Seed Demo Data` button to populate the demo immediately, or run `edge/mock_telemetry.py` for live updates.

## Design Notes

- The UI is plain HTML/CSS/JavaScript to avoid a package install during the hackathon sprint.
- The route maps are low-bandwidth schematics, matching the roadmap constraint that low-RAM Android devices should not depend on heavy live map rendering.
- The LED strip visual uses the same backend tier names as the edge and telemetry layers.
