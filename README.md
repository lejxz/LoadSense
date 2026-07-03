# LoadSense

> **Real information. Safer rides. Smarter cities.**

Integrated AI occupancy and transit intelligence for public utility vehicles (PUVs) — an Edge-AI + Cloud platform that tells commuters whether an arriving jeepney has room, gives operators live fleet safety, and gives cities the demand data Google Maps cannot. Built by **Team FlowerBoys** (University of San Jose–Recoletos, Cebu) for the ASEAN AI Hackathon 2026 Smart Cities track, where it placed in the top 6 of its track and the top 40 overall.

<!-- TODO: hero.png — wide hero image. Suggested: a split frame showing the commuter app's phone UI (left) and the operator console (right), with the LoadSense wordmark centered on a deep-navy background. Save to docs/images/hero.png -->

---

## The Problem

Cebu's commuters, operators, and regulators all operate blind on the one variable that matters most: **how full is the next jeepney?**

- **PHP 3.5 billion a day** — the estimated daily cost of traffic congestion to the Philippine economy.
- **20+ minutes** spent at stops waiting for a ride that may already be full — and there is no way to know until the jeepney pulls up.
- **"Sabit" overloading** — passengers hanging off the back or sitting on the roof — is illegal, dangerous, and routine, because drivers are paid per head and there is no live capacity signal.
- **Operators** can't see which routes are over- or under-served at which hours, so fleet allocation is gut-feel.
- **LGUs** have no city-wide compliance dashboard to enforce PUV modernization policy.

Google Maps and existing transit apps show *where* a jeepney is on the map. None of them show *whether you can actually fit inside it.* LoadSense closes that gap, and aligns with **UN SDG 9** (industry, innovation, infrastructure) and **SDG 11** (sustainable cities and communities).

---

## The Solution

LoadSense is a two-layer platform that turns every PUV into a real-time occupancy sensor.

**Layer 1 — Edge AI (in-vehicle).** An overhead camera runs a YOLOv8-nano model fully offline, performing bidirectional passenger counting as people board and alight. The current count is mapped to a four-tier occupancy state and displayed on a **windshield LED strip** so waiting commuters can see — at a glance, from across the street — whether to flag this jeepney down or wait for the next one.

**Layer 2 — Cloud Intelligence.** A FastAPI backend ingests GPS + occupancy telemetry, predicts ETA, detects route deviations and driving anomalies, forecasts demand by route and time of day, fires operator-first safety alerts, and powers a context-aware boarding-assistant chatbot. Two browser front-ends sit on top: a commuter mobile app and an operator console.

> _This repository contains the software-only demo: the edge layer is implemented as a contract-faithful simulator (see `edge/line_crossing_counter.py` and `edge/mock_telemetry.py`). The cloud layer, both front-ends, the ML models, and the operator verification workflow are fully implemented._

---

## Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                                   INPUTS                                     │
│            Overhead camera frames  ·  GPS pings  ·  route geometry           │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              LAYER 1 — EDGE                                  │
│   YOLOv8-nano (offline, on-device)  →  bidirectional line-crossing counter   │
│   →  4-tier occupancy state  →  windshield LED strip (🟢 🟡 🔴 🔴-blink)       │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │  telemetry (GPS + occupancy tier + count)
                                ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                           LAYER 2 — CLOUD                                    │
│   FastAPI  ·  SQLite persistence  ·  live fleet state                        │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│   │ ETA model   │  │ Demand       │  │ Route-       │  │ Driving-anomaly  │  │
│   │ (XGBoost)   │  │ forecast     │  │ deviation    │  │ detector         │  │
│   │             │  │ (Prophet)    │  │ (200 m geof.)│  │ (speed + route)  │  │
│   └─────────────┘  └──────────────┘  └──────────────┘  └──────────────────┘  │
│        + NLP boarding-assistant chatbot  +  operator alert workflow          │
└───────────────────────────────┬──────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
┌──────────────────────────────┐   ┌──────────────────────────────────────────┐
│      COMMUTER MOBILE APP     │   │          OPERATOR CONSOLE                │
│  · live map w/ color-coded   │   │  · fleet summary + live vehicle list    │
│    PUV markers               │   │  · demand-forecast bars                  │
│  · ETA + occupancy tier      │   │  · anomaly alerts                        │
│  · route list                │   │  · alert verification workflow           │
│  · boarding-assistant chat   │   │    (ack → verify → false-alarm /         │
│                              │   │     escalate)                            │
└──────────────────────────────┘   └──────────────────────────────────────────┘
```

<!-- TODO: architecture.png — render the diagram above as a clean vector image (Figma / Excalidraw / diagrams.net). Save to docs/images/architecture.png and replace the ASCII block with the image once it's ready. -->

---

## Features

| | Feature | What it does |
|---|---|---|
| 🟢🟡🔴🔴-blink | **Four-tier occupancy display** | Classifies every PUV as Available / Filling up / At capacity / Overloaded and reflects it on a windshield LED strip + commuter-app marker. |
| 📍 | **Live fleet map** | Color-coded jeepney markers on real Cebu routes, drawn over Leaflet + OpenStreetMap. |
| ⏱️ | **ETA prediction** | Gradient-boosted (XGBoost) model trained on synthetic historical logs; per-vehicle ETA to any stop on the route. |
| 📈 | **Demand forecasting** | Prophet time-series model predicts ridership by route × hour, feeding operator allocation decisions. |
| 🛡️ | **Route-deviation & driving-anomaly alerts** | 200 m geofence per route; speed-limit and harsh-event detection trigger operator alerts. |
| ✅ | **Operator-first alert verification** | Every alert goes through a structured ack → verify → mark-false-alarm / escalate workflow — no black-box auto-escalation. |
| 💬 | **Boarding-assistant chatbot** | Natural-language "which jeepney is least crowded right now?" queries over live fleet state. |
| 🌏 | **ASEAN scalability** | Country seed data for PH / ID / MY / TH / VN; GTFS import path for non-Cebu cities. |

<!-- TODO: features_grid.png — 2×4 grid of the eight features above, each cell with an icon + 1-line description. Save to docs/images/features_grid.png. -->

### Screenshots

<!-- TODO: screenshot_commuter_map.png — phone-shaped screenshot of mobile.html showing the live Cebu map with at least 3 jeepney markers (one green, one yellow, one red), an open route list, and an ETA badge. -->

<!-- TODO: screenshot_chatbot.png — phone-shaped screenshot of the boarding-assistant chatbot answering "Which jeepney is least crowded right now?" with a referenced route code and tier. -->

<!-- TODO: screenshot_operator_console.png — wide screenshot of operator.html showing the fleet table, demand-forecast bar chart, and at least one open alert in the verification workflow. -->

<!-- TODO: demo.gif — 15-20 second screen recording cycling through: commuter map → tap a PUV → open chatbot → switch to operator console → acknowledge an alert. -->

---

## Quick Start

### Prerequisites

- Python 3.11+
- `pip install -r requirements.txt`

### Run the demo

```bash
# 1. From the repo root, start the FastAPI server.
#    On startup it auto-launches a looping synthetic Cebu PUV fleet —
#    no hardware, no camera, no GPS dongle required.
uvicorn backend.app.main:app --reload --port 8000

# 2. Open the landing portal in your browser:
#       http://localhost:8000
#    It links to:
#       /mobile.html    → Commuter app
#       /operator.html  → Operator console
```

### Optional: extra telemetry stream

```bash
# Stream mock GPS + occupancy telemetry over WebSocket (simulates a second PUV).
python edge/mock_telemetry.py --mode ws --interval 2
```

### Optional: generate edge line-crossing evidence

```bash
# Simulate 240 frames of bidirectional passenger counting and export the
# resulting per-frame counts + derived LED tier to CSV.
python edge/line_crossing_counter.py --frames 240
```

### Run with Docker

```bash
docker compose up --build
# Same URLs as above.
```

### Optional: enable the Gemini-powered chatbot

```bash
cp .env.example .env
# Add GEMINI_API_KEY=... to .env
# Without a key, the demo falls back to the no-API context-based chatbot
# so the boarding-assistant feature still works offline.
```

---

## API Highlights

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/fleet` | Live fleet state — every PUV's current location, occupancy tier, and ETA. |
| `GET` | `/api/routes` | List of Cebu routes with geometry. |
| `GET` | `/api/eta/{vehicle_id}` | Predicted ETA for a vehicle to its remaining stops. |
| `GET` | `/api/demand/forecast` | Prophet demand forecast per route × hour. |
| `GET` | `/api/alerts` | Open operator alerts (route deviation, anomaly, overload). |
| `POST` | `/api/alerts/{id}/ack` | Acknowledge an alert (start of verification workflow). |
| `POST` | `/api/alerts/{id}/verify` | Mark an alert as a real incident. |
| `POST` | `/api/alerts/{id}/false-alarm` | Mark an alert as a false alarm. |
| `POST` | `/api/alerts/{id}/escalate` | Escalate an alert for human review. |
| `POST` | `/api/chatbot` | Boarding-assistant NLP query. |
| `WS` | `/ws/fleet` | Live fleet telemetry stream for the commuter map. |

Full request/response schemas are in the FastAPI auto-docs at `http://localhost:8000/docs`.

### Verification

```bash
python tests/run_health_check.py        # backend health
python tests/run_api_smoke.py           # core REST endpoints
python tests/run_chatbot_regression.py  # boarding-assistant fixtures
python tests/run_demo_state_check.py    # demo simulator integrity
```

---

## Built With

**Backend** — Python 3.11 · FastAPI · Uvicorn · Pydantic v2 · SQLite · WebSockets

**Machine Learning** — XGBoost (ETA) · Prophet (demand) · scikit-learn · pandas

**Edge (planned / simulated)** — YOLOv8-nano (Ultralytics) on Raspberry Pi 5 / Jetson Nano

**Frontend** — Vanilla HTML / CSS / JavaScript (no build step) · Leaflet · OpenStreetMap · Photon geocoder

**Tooling** — Docker · docker-compose · Google Gemini (optional, for the LLM chatbot)

---

## Project Layout

```text
LoadSense/
├── backend/              # FastAPI app, core logic, DB, ML model wiring
│   └── app/
│       ├── main.py              # app entry, lifespan demo simulator
│       ├── api/routes.py        # all REST + WebSocket endpoints
│       ├── core/                # transit, occupancy, route-deviation,
│       │                        # demo_simulator, chatbot, alerts
│       └── db/sqlite_store.py   # persistence layer
├── app/                 # Browser UI (vanilla HTML/CSS/JS)
│   ├── index.html               # role launcher
│   ├── mobile.html              # commuter app
│   ├── operator.html            # operator console
│   └── vendor/leaflet/          # vendored map library
├── edge/                # Software-only edge simulation
│   ├── mock_telemetry.py        # GPS + occupancy telemetry generator
│   └── line_crossing_counter.py # bidirectional passenger counter sim
├── cloud/               # Phase 2 model training
│   ├── train_eta_model.py       # → artifacts/eta_model.pkl
│   └── train_demand_forecast.py # → artifacts/demand_forecast.json
├── data/                # Synthetic logs + ASEAN seed data
├── config/              # project_config.json (capacity, thresholds)
├── docs/                # Pitch outline, ethics report, requirements coverage, phase runbooks
├── tests/               # Health / smoke / chatbot / demo-state checks
├── tools/               # Cebu route generation + scraping
├── CONCEPT.md           # Full technical roadmap
├── RUN_DEMO.md          # Demo runbook
├── Dockerfile
└── docker-compose.yml
```

---

## Documentation

- [`CONCEPT.md`](./CONCEPT.md) — Full technical roadmap: architecture, models, data strategy, ethics, milestones.
- [`RUN_DEMO.md`](./RUN_DEMO.md) — Step-by-step demo runbook.
- [`docs/loadsense_pitch_outline.md`](./docs/loadsense_pitch_outline.md) — 5-minute pitch video script.
- [`docs/AI_USE_ETHICS_REPORT.md`](./docs/AI_USE_ETHICS_REPORT.md) — AI use and ethics report.
- [`docs/DATA_SOURCES_AND_APIS.md`](./docs/DATA_SOURCES_AND_APIS.md) — Data sources, licenses, and external APIs.
- [`docs/REQUIREMENTS_COVERAGE.md`](./docs/REQUIREMENTS_COVERAGE.md) — Hackathon requirements coverage matrix.
- [`docs/phase-1.md`](./docs/phase-1.md) … [`docs/phase-5.md`](./docs/phase-5.md) — Per-phase build runbooks.

---

## Team

**Team FlowerBoys** — University of San Jose–Recoletos (USJR), Cebu, Philippines.

| Member | Role | GitHub |
|---|---|---|
| Kent (lejxz) | Backend, ML, edge simulation, lead | [@lejxz](https://github.com/lejxz) |
| Perejan (hansandreperejan24-hash) | Frontend, operator console | [@hansandreperejan24-hash](https://github.com/hansandreperejan24-hash) |
| Pycnosis | Frontend, commuter app | [@Pycnosis](https://github.com/Pycnosis) |

<!-- TODO: team.png — optional team photo or avatar row, save to docs/images/team.png. -->

---

## Data Sources & Acknowledgements

- **OpenStreetMap & Overpass API** (ODbL) — base map and route geometry.
- **Cebu Jeepneys route reference** (CC BY-NC 3.0) — route codes and stop lists.
- **Photon geocoder** (Apache 2.0, Komoot) — place search.
- **Google Fonts** — Manrope + Sora typefaces.
- Synthetic historical occupancy logs and edge line-crossing counts were generated by the team — see `data/generate_synthetic_history.py`.

---

## Limitations & Future Work

This repository is a hackathon prototype. The cloud layer, both browser front-ends, the ML models, the operator alert workflow, and the boarding-assistant chatbot are fully implemented. The edge layer is implemented as a **contract-faithful simulator**: it produces the same count + occupancy-tier data structure that a real YOLOv8-nano deployment would emit, but does not run real video inference and is not wired to physical hardware. Real GPS, live weather, and external LLM calls are not required to run the demo.

Roadmap items beyond the current prototype:

- Real YOLOv8-nano video inference on Raspberry Pi 5 / Jetson Nano.
- Live GPS telemetry from onboard modules.
- OpenWeatherMap integration for weather-aware ETA features.
- External LLM-backed chatbot (Gemini key is already wired optionally).
- GTFS import pipeline for non-Cebu ASEAN cities (seed data for ID / MY / TH / VN already in `data/countries/`).

See `CONCEPT.md` for the full roadmap and per-phase milestones.

---

## License

No license has been declared yet. All rights are reserved by the contributors by default; contact the team for licensing inquiries. A permissive license (e.g. MIT) is recommended for future open-sourcing.
