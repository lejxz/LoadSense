# LoadSense Prototype Task Breakdown (Software-Only)

> Hardware-free hackathon sprint. The edge layer is simulated via mock data and laptop inference.

---

## Legend
- `[SIMULATED]` — replaces hardware with mock data
- `[CORE LOGIC]` — actual model/backend code
- `[UI/DEMO]` — frontend & visualization
- `[WRAP-UP]` — polish & pitch

---

## Phase 1 — Foundation: Mock Data + Project Setup

1. `[WRAP-UP]` Set up Python project structure: `edge/`, `cloud/`, `app/` folders with a shared `requirements.txt`
2. `[SIMULATED]` Write a **mock telemetry generator** — a script that outputs fake GPS coordinates + occupancy counts (0–16) to a JSON/WebSocket stream, simulating the Raspberry Pi feed
3. `[CORE LOGIC]` Define occupancy thresholds in a config: Green ≤50%, Yellow ≤75%, Red ≤100%, Blinking Red >100%
4. `[SIMULATED]` Generate or download a CSV of **synthetic historical occupancy logs** (timestamps + route + count) — at least 500 rows — to train ETA and demand models later

---

## Phase 2 — Cloud Backend: ETA + Demand Models (FastAPI)

5. `[CORE LOGIC]` Train a **Gradient Boosting ETA model** (XGBoost/scikit-learn) on the synthetic CSV — features: GPS stop index, time-of-day, simulated traffic factor. Export as `.pkl`
6. `[CORE LOGIC]` Train a **Facebook Prophet demand forecast model** on the same CSV — output: predicted load per stop per hour. Export forecasts as a JSON file for the dashboard
7. `[CORE LOGIC]` Build a **FastAPI server** with three endpoints: `POST /telemetry` (receives mock GPS+occupancy), `GET /eta/{stop_id}`, `GET /demand`
8. `[CORE LOGIC]` Add a simple **route deviation check**: if the incoming GPS coordinate deviates >200m from the expected polyline, flag it as an anomaly in the response JSON

---

## Phase 3 — Edge Simulation: YOLOv8-nano Inference (Laptop/Colab)

9. `[CORE LOGIC]` Run **YOLOv8-nano on a sample video** (a crowd/street clip from YouTube or your own footage) using Ultralytics Python SDK — count detected persons per frame and output counts to a CSV. This is your "edge AI" demo evidence
10. `[CORE LOGIC]` Write a **bidirectional line-crossing counter** script: define a horizontal line across the video frame, count persons crossing up vs. down, derive a running passenger count
11. `[SIMULATED]` Map the running count to the occupancy tier (Green/Yellow/Red/Blinking Red) and log state changes — this output feeds the LED simulation in the frontend

---

## Phase 4 — Frontend Prototype: Commuter App + Operator Dashboard

12. `[UI/DEMO]` Build a **commuter web app** (React Native Web or plain React) with: a route map (Leaflet.js), stop-level ETA from the FastAPI endpoint, and occupancy badge per vehicle
13. `[UI/DEMO]` Add an **LED strip visual** on the app — a horizontal bar that animates Green → Yellow → Red → Blinking Red based on live occupancy state from the mock telemetry stream
14. `[UI/DEMO]` Build an **operator dashboard** (separate page/tab): fleet list with occupancy status, demand forecast chart (Recharts/Chart.js from your Prophet output), and anomaly alerts panel
15. `[UI/DEMO]` Add an **NLP chatbot widget** (call an LLM API — OpenAI or Claude) that answers commuter queries like "Which jeepney is least crowded for Route 04-L right now?" using occupancy + ETA context injected into the system prompt

---

## Phase 5 — Integration + Demo: End-to-End Run + Pitch Video

16. `[CORE LOGIC]` Wire everything together: mock telemetry script → FastAPI → React dashboard running simultaneously. Confirm occupancy updates reflect in LED, ETA, and operator dashboard in near-real-time
17. `[WRAP-UP]` Run the YOLOv8 video through your counter, narrate the output as "what would happen on a real jeepney" — screenshot or screen-record the person count changing tiers
18. `[WRAP-UP]` Record the **demo video**: show the commuter app, the live LED simulation, the operator dashboard (with demand forecast), and a chatbot query — voice-over or on-screen captions
19. `[WRAP-UP]` Prepare pitch slides: Problem → Solution → Architecture diagram → Live demo screenshots → SDG alignment → ASEAN scalability. Keep to 5–7 slides

---

## Notes

- **Start with Phase 1 no matter what.** The mock telemetry generator is the backbone — Phases 2, 3, and 4 all depend on data flowing.
- **Phase 3 can run in parallel with Phase 2** if you split the team — YOLO inference and model training don't block each other.
- **The LED strip visual (Step 13) is your most impressive demo moment** — it replaces hardware and makes the prototype feel real to judges.
- **For the NLP chatbot (Step 15)**, inject current occupancy JSON into the system prompt — no RAG needed. Example: *"Current fleet state: Route 04-L, Vehicle J-214, occupancy: Red (14/16 passengers), ETA to Colon: 7 min."*
- **Don't build a mobile app** — a responsive React web app demos just as well in a browser and is far faster to build.