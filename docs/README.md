# LoadSense Docs

This folder collects the working notes and runbooks for the LoadSense software-only prototype.

## Sections

- [Requirements Coverage](REQUIREMENTS_COVERAGE.md)
- [Phase 1](phase-1.md)
- [Phase 2](phase-2.md)
- [Phase 3](phase-3.md)
- [Phase 4](phase-4.md)
- [Phase 5](phase-5.md)

## Roadmap Alignment

The implementation follows the PDF roadmap and `TaskSeparation.md`:

- Edge layer: simulated camera passenger counting and telemetry packaging.
- Cloud layer: FastAPI state processing, SQLite persistence, ETA, demand forecast, route safety, and operator-first alerts.
- User delivery: commuter app, operator dashboard, LED strip visual, and context-based chatbot response.

The current repo is intentionally hardware-free so it can be demoed on a laptop during the hackathon sprint.
