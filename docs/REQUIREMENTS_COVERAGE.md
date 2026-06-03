# Requirements Coverage

This file maps the architecture diagram and roadmap/PDF mirror in `CONCEPT.md` to the current software prototype.

The actual PDF could not be text-extracted in this environment because no local PDF extraction tool or Python PDF library is installed. `CONCEPT.md` is used as the checked-in roadmap mirror.

## Demo Boundaries

| Demo | Files | Purpose |
|---|---|---|
| Edge counting demo | `edge/line_crossing_counter.py`, `data/edge_line_crossing_counts.csv` | Simulates overhead camera line crossing, occupancy tiers, LED state, and zone density evidence. |
| Interface demo | `app/index.html`, `app/mobile.html`, `app/operator.html`, `app/demo.js`, `app/styles.css` | Shows commuter and operator experiences that consume backend telemetry. |
| Backend/cloud demo | `backend/`, `cloud/`, `data/loadsense_demo.sqlite` | Processes telemetry, predicts ETA, checks safety, persists history, and serves APIs. |

## Architecture Diagram Coverage

| Diagram item | Status | Implementation |
|---|---|---|
| GPS unit | Implemented as simulation | Backend startup runs looping synthetic PUV positions; `edge/mock_telemetry.py` can send extra route-aware latitude and longitude. |
| Overhead camera | Simulated | `edge/line_crossing_counter.py` produces frame-level person crossing evidence. |
| Commuter queries | Implemented | Mobile Chat tab calls `POST /api/chatbot`. |
| YOLOv8-nano inference | Simulated boundary | The repo does not run real YOLO; it emits the same downstream count/tier contract. |
| LED state controller | Implemented in software | Occupancy tiers map to green, yellow, red, and blinking red in edge output and UI. |
| Telemetry packager | Implemented | HTTP and WebSocket telemetry modes in `edge/mock_telemetry.py`. |
| FastAPI middleware | Implemented | `backend/app/main.py` and `backend/app/api/routes.py`. |
| ETA prediction | Implemented | `cloud/train_eta_model.py`, `backend/app/core/phase2.py`, fallback ETA when no model exists. |
| Demand forecasting | Implemented | `cloud/train_demand_forecast.py`, `cloud/artifacts/demand_forecast.json`, operator forecast chart. |
| Route and safety monitor | Implemented | Route deviation, GPS dropout, overload, overspeeding, and sudden-stop alerts. |
| NLP chatbot | Implemented as deterministic assistant | `POST /api/chatbot` uses live fleet context; no external LLM key is required for demo reliability. |
| Cloud database | Implemented | SQLite database at `data/loadsense_demo.sqlite`; route geometry is seeded from `data/cebu_osm_routes.geojson`, not config. |
| Operator dashboard | Implemented | `app/operator.html`. |
| Commuter app | Implemented | `app/mobile.html`. |
| Safety alerts | Implemented | Operator-first alert list, acknowledgement, and incident history. |
| Physical LED unit | Simulated | LED tiers appear in edge CSV and commuter app; physical GPIO is outside this laptop demo. |
| Feedback loop | Partially implemented | Operator acknowledgement is stored as feedback. Automatic model retraining is represented by training scripts, not background jobs. |

## Roadmap Feature Coverage

| Requirement | Status | Notes |
|---|---|---|
| Bidirectional passenger counting | Implemented as simulation | Crossing direction and running count are written to CSV. |
| Dynamic occupancy classification | Implemented | Shared thresholds in `backend/app/core/occupancy.py`. |
| External visual signaling | Simulated | LED tier shown in UI and edge CSV. |
| Zone-based heatmapping | Implemented as simulated zones | Edge CSV includes `zone` for front entrance, mid cabin, rear cabin. |
| GPS tracking | Implemented as simulation | Telemetry includes synthetic coordinates per vehicle and route; no real GPS hardware is required for the hackathon demo. |
| AI-predicted ETA | Implemented | Model artifact is used when available; fallback exists for demo. |
| Traffic/weather factor | Partially implemented | ETA supports a traffic factor; live OpenWeatherMap integration is not used in the offline demo. |
| Route deviation detection | Implemented | Off-route telemetry raises alerts. |
| Driving anomaly detection | Implemented | Overspeeding and sudden deceleration alerts were added. |
| Operator-first alert chain | Implemented | Alerts appear in operator console and must be verified before being treated as confirmed. |
| Historical incident flagging | Implemented | SQLite stores alerts and acknowledgements; `/api/incidents` exposes history. |
| Lightweight mobile app | Implemented | Phone-shaped low-bandwidth HTML/CSS/JS app. |
| Stop-level ETA and crowd density | Implemented | Mobile Home and route vehicle cards show ETA, stop index, and occupancy. |
| Mobile map UI | Implemented | Mobile Map tab draws route schematics and PUV pins. |
| Route list | Implemented | Mobile Routes tab shows one searched/selected route with concise Cebu route facts and sampled checkpoints. |
| AI boarding chatbot | Implemented | Mobile Chat tab calls backend recommendation endpoint. |
| Operator demand forecasting | Implemented | Operator console renders checked-in demand forecast artifact. |
| Proactive dispatch view | Implemented for demo | Operator forecast and fleet status support dispatch discussion; no automated dispatch optimizer is included. |
| Persistent database | Implemented | SQLite stores telemetry logs, latest fleet state, alerts, feedback, and chatbot queries. |

## Intentional Prototype Limits

- Real YOLO inference and physical GPIO LED control are outside the laptop demo.
- Live weather API calls are skipped so the demo works without network or API keys.
- The chatbot is deterministic for reliability; it can be replaced with an LLM API later.
- Model retraining is run manually through scripts rather than scheduled in the backend.
