# AI-Use And Ethics Report Draft

Team Name: USJR - FlowerBoys ASEAN

Institution: University of San Jose-Recoletos

Country: Philippines

Track: Smart Cities

Project Title: LoadSense: Integrated AI Occupancy and Transit Intelligence for PUVs

## 1. Introduction

LoadSense addresses a daily public-transport problem in Metro Cebu: commuters often wait for jeepneys and modern PUVs without knowing whether the next vehicle is full, delayed, or off-route. The current project demonstrates a software-only prototype that combines simulated passenger counting, synthetic GPS movement, ETA estimation, occupancy classification, route monitoring, demand forecasting, and commuter/operator interfaces.

AI and data-driven methods are useful because public-transport occupancy, demand, and arrival times change constantly. Static schedules or manual inspection cannot easily answer questions like which PUV is least crowded, which route is overloaded, or which vehicle may need operator review. LoadSense shows how low-cost retrofit intelligence could improve commuter visibility and operator decision-making while keeping the current prototype honest about its simulation boundaries.

## 2. Problem Context And Solution Overview

In Cebu and many ASEAN cities, jeepneys and modern PUVs remain affordable and familiar, especially for lower-income commuters. However, they usually do not provide real-time capacity, route status, or safety information. LoadSense supports commuters, drivers, operators, transport cooperatives, city traffic managers, and regulators by making vehicle state easier to see.

The current prototype has three parts. First, an edge simulation produces passenger count and occupancy-tier evidence. Second, a FastAPI backend stores telemetry in SQLite, tracks live fleet state, predicts ETA, flags overload and route/safety anomalies, and serves route data. Third, a browser-based commuter app and operator dashboard display route options, moving synthetic PUVs, crowding state, alerts, and boarding recommendations.

The current demo uses Cebu route geometry seeded from OpenStreetMap-derived GeoJSON and runs looping synthetic PUVs automatically. No real GPS device, real passenger camera, or physical LED hardware is required for the hackathon demo.

## 3. AI Tools And Methods Used

The implemented stack uses Python, FastAPI, SQLite, pandas, scikit-learn/XGBoost-style ETA modeling, Prophet demand-forecast artifacts, JavaScript/HTML/CSS interfaces, and local test scripts. The edge layer is simulated through a Python line-crossing counter that emits occupancy counts, zones, and LED-style tiers. The backend includes deterministic boarding-assistant logic that uses live fleet context instead of requiring an external LLM API.

Development support included GitHub, AI coding assistants, Docker Compose, pydantic, uvicorn, websockets, python-dotenv, python-multipart, httpx2, and an Ultralytics/YOLOv8-nano boundary in the planned edge architecture. The current repo does not claim real YOLO inference accuracy; it simulates the downstream count/tier contract needed by the rest of the system.

## 4. Assessment Of AI Output

Accuracy: The prototype is logically consistent for a hackathon demo. Health and API smoke checks cover telemetry, route data, fleet state, alerts, ETA, demand, database status, and chatbot endpoints. The live map and dashboard use Cebu-based coordinates and many synthetic PUV states. However, the movement, occupancy, and demand values are synthetic, so they validate integration behavior rather than real-world accuracy.

Bias: The system is Philippines-focused by design. This improves regional relevance but means the thresholds, route assumptions, and commuter wording may not transfer directly to other ASEAN cities without local calibration. The passenger-counting design counts movement and occupancy only; it does not classify gender, age, identity, or protected traits.

Cultural sensitivity: LoadSense keeps jeepneys and PUVs as the center of the system instead of assuming immediate fleet replacement. It uses familiar route codes and a map-style interface that commuters and judges can understand quickly. Safety alerts are treated as operator-first signals, not automatically public accusations.

Language: The boarding assistant can answer practical English, Tagalog, and Cebuano-style route questions in a limited deterministic way, but it is not yet a robust multilingual LLM. Future language expansion should be tested with Cebuano, Tagalog, English, and code-switched commuter prompts.

## 5. Human Intervention And Justification

Human review was essential. AI tools helped generate architecture ideas, code scaffolds, UI revisions, and documentation drafts, but the team corrected overclaims and aligned the project with the actual demo boundary: software-only, laptop-based, no real hardware, no real GPS, and no live passenger surveillance. The team also separated the edge counting evidence from the commuter/operator interface so the pitch can clearly explain what is simulated and what is operational in software.

Human judgment was used to remove fake route claims, seed route geometry into SQLite, revise the UI toward a familiar map interaction, and document that PUV markers are synthetic. This protects the project from overstating readiness or implying field-validated safety performance.

## 6. Data, APIs, And Licenses

See `docs/DATA_SOURCES_AND_APIS.md` for the complete citation inventory. The core current sources are OpenStreetMap/Overpass route geometry under ODbL, a local SQLite demo database, synthetic GPS/occupancy/demand data, optional Photon place search from OSM-derived data, Google Fonts for the browser UI, and project-created FastAPI endpoints.

## 7. Reflection On AI-Human Co-Creation

AI-human co-creation accelerated the prototype by helping generate backend routes, simulator logic, UI revisions, and report drafts. The main risk was plausibility without verification: AI sometimes suggested details that sounded correct but were not yet implemented or field-tested. The team learned to treat AI output as a draft that must be checked against code, tests, local transport context, and licensing obligations.

The final prototype is therefore a constrained demo, not a finished deployment claim. It shows a working edge-to-cloud software path while clearly separating synthetic data, implemented APIs, and future integrations.

## 8. Conclusion

LoadSense demonstrates how AI and real-time transit data can support safer, clearer, and more commuter-friendly public transport without replacing existing jeepney and PUV systems. The prototype shows how occupancy, ETA, route state, and operator alerts can work together in a practical Smart Cities demo. The ethical priority is to remain transparent: synthetic data is synthetic, safety alerts need human review, privacy must be protected, and real-world deployment requires local pilot validation.
