# LoadSense

LoadSense is a hackathon prototype for the ASEAN AI Hackathon 2026 Smart Cities track. It simulates an intelligent jeepney/PUV platform for Cebu, Philippines: software-only edge telemetry, a FastAPI cloud layer, an operator dashboard, and a commuter mobile UI.

All hardware is simulated. Passenger counting is a deterministic random walk, GPS follows Cebu route waypoints, LED strips render in the terminal and WebSocket, and AI/ML models fall back to demo logic when heavyweight packages are unavailable.

## Project Layout

```text
edge/            Simulated Raspberry Pi passenger counter, GPS, LEDs, telemetry POSTs
backend/         FastAPI API, SQLite seed data, ETA, demand, anomaly, chatbot routes
dashboard/       React + Vite operator dashboard on port 5173
commuter-app/    React + Vite mobile commuter app on port 5174
docker-compose.yml
```

## Run Without Docker

Use Python 3.11+ and Node 20+.

```powershell
python -m venv venv
venv\Scripts\pip install -r requirements.txt
venv\Scripts\python backend\seed.py
cd backend
..\venv\Scripts\uvicorn main:app --reload --port 8000
```

In two more terminals:

```powershell
cd dashboard
npm install
npm run dev
```

```powershell
cd commuter-app
npm install
npm run dev
```

Start the simulated edge devices:

```powershell
venv\Scripts\python edge\simulator.py --vehicles 3
```

Open the apps:

- Operator dashboard: http://localhost:5173
- Commuter app: http://localhost:5174
- Backend docs: http://localhost:8000/docs

## Run With Docker

```powershell
docker compose up --build
```

Then run the edge simulator from the host:

```powershell
python edge\simulator.py --vehicles 3 --backend-url http://127.0.0.1:8000
```

## Local Chatbot

The commuter chatbot is fully local for the prototype. It uses the nearest live jeepney, occupancy tier, passenger count, ETA estimate, and selected stop to return a deterministic 2-sentence boarding recommendation. No Claude, Anthropic, OpenAI, or other paid API key is required.

## Demo Walkthrough Script

1. Start the backend, dashboard, commuter app, and edge simulator with `python edge\simulator.py --vehicles 3`.
2. Show the simulator terminal: LED states update every two seconds in green, yellow, red, or blinking red.
3. Open http://localhost:5173 and show three jeepneys moving on the Cebu Fleet Map.
4. Trigger a route anomaly with `python edge\simulator.py --vehicles 3 --force-deviation`; `JY-001` moves off-route.
5. Open Alerts, show the `ROUTE_DEVIATION` alert, click Acknowledge, and narrate that commuters are now notified.
6. Open Demand, select Ayala-SM-Carbon, and show the six-window rush-hour forecast.
7. Open http://localhost:5174, select a stop, and compare incoming jeepneys by ETA and occupancy.
8. In Chat, ask "Should I board the next jeepney?" and show the recommendation using live occupancy context.
9. Open Map and show nearby jeepney dots around the selected Cebu stop.

## API Highlights

- `POST /api/telemetry`
- `GET /api/fleet`
- `GET /api/eta/{vehicle_id}/{stop_id}`
- `GET /api/demand/{route_id}`
- `GET /api/anomalies`
- `PATCH /api/anomalies/{id}`
- `POST /api/chat`
- `GET /api/ws` as a WebSocket endpoint
