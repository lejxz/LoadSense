# Phase 3: Edge Simulation

Status: complete for software-only demo

## What Phase 3 Adds

- `edge/mock_telemetry.py` simulates GPS and occupancy payloads from a vehicle.
- `edge/line_crossing_counter.py` simulates a bidirectional line-crossing passenger counter.
- `data/edge_line_crossing_counts.csv` stores generated frame-level count evidence.

## Run Mock Telemetry

Print payloads:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode stdout --limit 5
```

Send payloads to FastAPI:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode http --url http://localhost:8000/api/telemetry --interval 1
```

Send payloads over WebSocket:

```powershell
venv\Scripts\python.exe edge\mock_telemetry.py --mode ws --url ws://localhost:8000/api/ws/telemetry --interval 1
```

## Run Line-Crossing Demo

```powershell
venv\Scripts\python.exe edge\line_crossing_counter.py --frames 240 --output data\edge_line_crossing_counts.csv
```

The CSV contains frame number, simulated centroid position, crossing direction, running passenger count, and LED tier.

## Hardware Boundary

The roadmap calls for YOLOv8-nano on Raspberry Pi 5 or Jetson Nano. This repo keeps the edge layer hardware-free for laptop demo reliability. The counter output matches the downstream contract that real YOLO tracking would produce: a running occupancy count and tier.
