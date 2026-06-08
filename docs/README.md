# LoadSense Docs

This folder collects the working notes and runbooks for the LoadSense software-only prototype.

## Sections

- [Demo Runbook](../RUN_DEMO.md)
- [Requirements Coverage](REQUIREMENTS_COVERAGE.md)
- [Data Sources And API Citations](DATA_SOURCES_AND_APIS.md)
- [AI-Use And Ethics Report Draft](AI_USE_ETHICS_REPORT.md)
- [Phase 1](phase-1.md)
- [Phase 2](phase-2.md)
- [Phase 3](phase-3.md)
- [Phase 4](phase-4.md)
- [Phase 5](phase-5.md)

## Current Prototype Boundary

The current implementation follows the checked-in roadmap while keeping the hackathon demo software-only:

- Edge layer: simulated camera passenger counting and telemetry packaging.
- Cloud layer: FastAPI state processing, SQLite persistence, ETA, demand forecast, route safety, and operator-first alerts.
- User delivery: browser commuter app, browser operator dashboard, simulated LED/occupancy tier visual, and context-based chatbot response.

No real GPS hardware, physical LED unit, live weather API, external LLM call, or real YOLO video inference is required for the current local demo.
