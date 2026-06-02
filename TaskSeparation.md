
---

## LoadSense Prototyping — Task Breakdown

### Part 1: Backend Foundation
**Build before anything else — everything depends on this.**

- Set up FastAPI server with basic routes
- Define the data schema for GPS + occupancy payloads
- Set up the cloud database (PostgreSQL or SQLite for prototype)
- Accept and store incoming telemetry from the edge device
- Test with mock data (no real hardware needed yet)

---

### Part 2: ETA + Demand Forecasting Models
**Once data flows in, train the models.**

- Prepare training data (OpenStreetMap + historical GPS logs + OpenWeatherMap)
- Train the Gradient Boosting (XGBoost) ETA model
- Train the Prophet demand forecasting model
- Expose both as FastAPI endpoints
- Validate output with explicit confidence bounds during cold-start

---

### Part 3: Frontend Interfaces
**Build the user-facing layer on top of working API endpoints.**

- Commuter mobile app (React Native)
  - Stop-level ETA display
  - Occupancy status (Green/Yellow/Red/Blinking Red)
  - AI chatbot interface (connect to LLM API)
  - Tile-based static map (not full interactive — low-RAM target)
- Operator dashboard
  - Fleet dispatching alerts
  - Demand forecast view
  - Incident log

---

### Part 4: End-to-End Integration + Edge Case Handling
**Connect everything and stress test it.**

- Connect edge device telemetry to the live backend
- Integrate GPIO LED state into the full data loop
- Test GPS dropout handling (dead-reckoning fallback)
- Test low-light detection failure cases
- Run Pytest + GitHub Actions for automated checks
- Fix breaking points between edge, cloud, and frontend

---

### Part 5: Demo Video + Pitch Preparation
**Last — only after the prototype is stable.**

- Record a demo walkthrough (edge AI counting → LED output → app ETA → operator dashboard)
- Prepare slides if needed
- Write the pitch script focused on the problem-solution fit from Section 1

---

**Honest note:** Part 4 will likely take the longest. Integration bugs between the edge device, FastAPI server, and frontend are where most prototype time gets consumed. Do not leave Part 4 for the last two days before the deadline.