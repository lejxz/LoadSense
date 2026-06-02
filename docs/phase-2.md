# Phase 2: Cloud Backend

Status: started

## What Phase 2 Adds

- A trainable ETA model based on the synthetic occupancy history
- A Prophet-based demand forecast JSON artifact for the dashboard
- A route deviation anomaly check in the telemetry endpoint
- API endpoints that read the generated artifacts when available

## Run Steps

Generate the ETA model:

```powershell
venv\Scripts\python.exe cloud\train_eta_model.py
```

Generate the demand forecast:

```powershell
venv\Scripts\python.exe cloud\train_demand_forecast.py
```

Send mock telemetry with route-aware GPS points:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --route 04L --url ws://localhost:8000/ws/telemetry
```

Start the backend:

```powershell
$env:PYTHONPATH='.'; uvicorn backend.app.main:app --reload --app-dir backend
```

Test ETA:

```powershell
Invoke-RestMethod "http://localhost:8000/api/eta/3?time_of_day=8.5&traffic_factor=1.2&route=04L"
```

Test demand:

```powershell
Invoke-RestMethod "http://localhost:8000/api/demand"
```

Test telemetry anomaly detection:

```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/api/telemetry" -ContentType "application/json" -Body '{"vehicle_id":"J-001","route":"04L","latitude":14.6100,"longitude":120.9950,"occupancy":9,"timestamp":"2026-06-02T00:00:00Z"}'
```
