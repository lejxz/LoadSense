# Phase 5: Integration and Demo

Status: complete for local prototype

## End-to-End Demo Script

1. Start the backend.

```powershell
$env:PYTHONPATH='.'; venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

2. Open the frontend at `http://localhost:8000`.
3. Open `http://localhost:8000/mobile.html` and sign in to the commuter app.
4. Open `http://localhost:8000/operator.html` for the operator console.
5. Seed demo data from either interface.
6. Ask the boarding assistant: `Which jeepney is least crowded right now?`
7. Run live telemetry in another terminal.

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

8. Generate edge counter evidence.

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240
```

## Verification

Run the health check:

```powershell
venv\Scripts\python.exe tests\run_health_check.py
```

Expected output:

```text
status_code: 200
body: {'status': 'ok'}
```

## Pitch Coverage

- Problem: blind waiting, overloading, inefficient dispatch.
- Solution: edge passenger counting plus cloud transit intelligence.
- Architecture: camera and GPS inputs, telemetry backend, ETA/demand/safety services, commuter and operator outputs.
- Demo: live LED tier, fleet dashboard, route deviation alert, demand chart, chatbot recommendation.
- Database: SQLite telemetry, latest vehicle state, alert, feedback, incident, and chatbot logs.
- SDG alignment: SDG 9 and SDG 11.
- ASEAN scalability: hardware-agnostic retrofit, low-bandwidth UI, cooperative/operator adoption path.

## Known Demo Limits

- The edge counter is simulated and does not run YOLO inference on real video in this repo.
- The chatbot is deterministic and context-based; no external LLM key is required.
- SQLite persists local demo state in `data/loadsense_demo.sqlite`.
- Demand forecasting uses the checked-in artifact unless the training script is rerun.
