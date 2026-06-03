# LoadSense Demo Runbook

This repo has two separate demo surfaces:

1. Edge counting demo: vehicle-side passenger counting evidence.
2. Interface demo: commuter mobile app and operator console.

They should be shown separately in the hackathon pitch because they represent different layers of the architecture diagram.

## 1. Setup

Windows PowerShell:

```powershell
python -m venv venv
& venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

For a lighter UI/API-only demo:

```powershell
pip install fastapi uvicorn[standard] pydantic websockets python-dotenv
```

## 2. Start The Interface Demo

```powershell
$env:PYTHONPATH='.'; & venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

Or start the backend and mock telemetry in two terminals:

```powershell
.\run_demo.ps1
```

Open:

```text
http://localhost:8000/
http://localhost:8000/mobile.html
http://localhost:8000/operator.html
```

Use `http://localhost:8000/` as the launcher. Use the other two URLs when presenting each role directly.

## 3. Automatic Synthetic Telemetry

Fastest path:

- Start the backend.
- Open the commuter or operator page.
- The backend automatically runs a software-only fleet demo: at least three ghost PUVs loop through each SQLite Cebu route and publish normal telemetry records.

Optional extra telemetry path:

```powershell
& venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

WebSocket path:

```powershell
& venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/api/ws/telemetry --interval 1
```

## 4. Run The Edge Counting Demo

Run this in a separate terminal:

```powershell
& venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240 --output data\edge_line_crossing_counts.csv
```

Webcam path:

```powershell
& venv\Scripts\python.exe edge\line_crossing_counter.py --source webcam --camera-index 0 --duration-seconds 90 --export both --url http://localhost:8000/api/telemetry
```

Video-file path:

```powershell
& venv\Scripts\python.exe edge\line_crossing_counter.py --source video --video data\sample_vehicle_video.mp4 --frames 1800 --export csv --output data\edge_line_crossing_counts.csv
```

This writes frame-level evidence with:

- crossing direction: `boarding` or `alighting`
- running occupancy count
- occupancy tier: green, yellow, red, blinking red
- simulated density zone: front entrance, mid cabin, rear cabin

This is intentionally separate from the browser app. In the real system it would run on the Raspberry Pi 5 or Jetson Nano. With `--export http` or `--export both`, the script POSTs occupancy telemetry to `POST /api/telemetry`; the backend persists it to SQLite and it appears in `/api/fleet`, `/api/database/status`, the commuter map, and the operator console.

No real edge hardware or GPS is required for this hackathon demo. The PUV map uses hardcoded synthetic movement along public Cebu route geometry, while the counting demo simulates the edge camera path on the laptop.

## 5. Docker Compose

```powershell
docker compose up --build
```

Open:

```text
http://localhost:8000/
http://localhost:8000/mobile.html
http://localhost:8000/operator.html
```

## 6. Route Data

The default route database is seeded from `data/cebu_osm_routes.geojson`, generated from OpenStreetMap Overpass route/corridor data for Cebu. Route code references were cross-checked against public Cebu jeepney route listings, including OpenStreetMap's Metro Cebu public transport wiki and Cebu Jeepneys route pages.

Operator UI import path:

1. Open `http://localhost:8000/operator.html`.
2. In `Route database`, choose a `.geojson`, `.csv`, or GTFS `.zip`.
3. Press `Preview file`.
4. If validation passes, press `Commit file`.

API path:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/api/routes/import `
  -Form @{ file = Get-Item .\data\routes.geojson; commit = "false"; replace = "false" }
```

Expected geometry formats:

- GeoJSON `FeatureCollection` with `LineString` or `MultiLineString` features.
- CSV with `route` or `route_id`, `name` or `route_name`, and `latitude`/`longitude` columns.
- GTFS zip with `shapes.txt`; `routes.txt` and `trips.txt` are used when present.

## 7. Database Check

The backend uses SQLite for the local cloud database:

```text
data/loadsense_demo.sqlite
```

Check it through the API:

```powershell
Invoke-RestMethod http://localhost:8000/api/database/status
Invoke-RestMethod http://localhost:8000/api/incidents
```

The operator console also displays table counts and the incident log.

## 8. Validation

```powershell
& venv\Scripts\python.exe tests\run_health_check.py
& venv\Scripts\python.exe tests\run_api_smoke.py
```

Expected:

```text
status_code: 200
api smoke ok
```

## 9. Pitch Order

1. Show the architecture diagram.
2. Run the edge counting demo and open `data/edge_line_crossing_counts.csv`.
3. Open the commuter mobile app and show login, Home, Map, Routes, and Chat.
4. Open the operator console and show fleet status, demand forecast, alerts, database counts, and incident log.
5. Acknowledge an alert to show operator-first verification.
