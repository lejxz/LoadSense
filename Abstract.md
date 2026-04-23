# LoadSense: Integrated AI Occupancy and Transit Intelligence for PUVs
> Asean AI Hackaton AAIH 2026

**Track Alignment:** Smart City — Intelligent Transportation & Urban Sustainability

---

## Overview

A dual-layer intelligent transportation system that combines lightweight, edge-based computer vision (inside the vehicle) with GPS-based transit network intelligence (outside the vehicle). By monitoring real-time occupancy via deep learning and predicting route arrivals via AI, the system provides immediate, actionable feedback to drivers, waiting commuters, and transport operators.

---

## The Problem

Public transit in ASEAN cities — particularly both informal and modern networks common in Cebu, Philippines — operates with no real-time visibility on either side of the vehicle door, creating daily friction for millions of commuters.

- **The Commuter's Information Gap:** Passengers cannot see a vehicle's interior state before it arrives, nor do they know exactly when it will arrive. Waiting is blind, delays are unannounced, and boarding decisions are reduced to a guessing game.
- **Inefficiency and Resource Waste:** Frequent, fruitless stops for full vehicles waste fuel and disrupt traffic flow. Without historical demand or route data, operators cannot efficiently allocate vehicles, leading to systemic urban congestion.
- **Safety and Regulatory Risks:** A lack of real-time monitoring leads to illegal overloading (e.g., *sabit*). Furthermore, unpredictable routes and unmonitored driving behavior (overspeeding, sudden stops) increase accident risks and legal liabilities without proper enforcement tools.

---

## The Solution

LoadSense integrates two complementary technologies into one platform to close the information gap entirely. It pairs an overhead-mounted camera and edge computing device — handling offline CV occupancy tracking — with a GPS telemetry and AI prediction layer. Designed to be easily retrofitted into any vehicle type, from modern buses to traditional open-air jeepneys, this allows commuters to know not only when the next vehicle is arriving, but whether there is space for them when it does.

---

## SDG Alignment

- **SDG 9 (Industry, Innovation, and Infrastructure):** Modernizes existing PUV infrastructure via an additive AI layer without requiring immediate fleet replacement.
- **SDG 11 (Sustainable Cities and Communities):** Reduces unnecessary stops, improves route throughput, and creates intelligent, accessible urban transport.

---

## Core Features

### 1. Occupancy & Edge AI (In-Vehicle)

- **Bidirectional Passenger Counting:** Utilizes a YOLOv8-nano model to track "Line Crossing" events and maintain a live headcount.
- **Dynamic Occupancy Classification:** Categorizes the vehicle state into four visual tiers:
  - 🟢 **Green** — Seats available
  - 🟡 **Yellow** — Standing only
  - 🔴 **Red** — At capacity
  - 🔴 **Blinking Red** — Overloaded
- **External Visual Signaling:** An LED strip mounted on the windshield changes color based on the occupancy state, visible to commuters from a distance.
- **Zone-Based Heatmapping:** Tracks spatial density over time to identify entrance crowding and refine counting accuracy.

### 2. Transit Intelligence & Prediction (Network)

- **GPS Tracking:** Real-time vehicle position broadcast to the network.
- **AI-Predicted ETA:** Server-side prediction of arrival times using live GPS position, traffic flow, weather, and historical patterns.
- **Route Deviation Detection:** Automatically flags when a vehicle goes off its expected path.

### 3. Safety & Compliance Layer

- **Driving Anomaly Detection:** Monitors for overspeeding, sudden stops, and unexpected detours.
- **Structured Alert Chain:** Alerts are sent to operators and dispatchers first for verification. Passengers are informed only once the information is accurate, preventing panic.
- **Historical Incident Flagging:** Builds an auditable safety and compliance record per vehicle and driver.

### 4. Commuter Interface

- **Lightweight Mobile App:** Optimized for low-bandwidth conditions and low-end Android devices common among target users.
- **Stop-Level Estimates & Crowd Density:** Displays actionable arrival times and passenger occupancy per approaching vehicle.
- **AI-Assisted Decision Chatbot:** A natural-language interface where users can ask, *"Should I board this jeep or wait for the next?"* The system processes the driver's current location, ETA, and LoadSense occupancy data to output a concrete, data-backed boarding recommendation.

### 5. Operator Demand Forecasting (Server-Side AI)

- **Time-Series Peak Prediction:** Uses historical passenger counting logs produced by the LoadSense edge system to train a predictive model. It forecasts when and where the highest number of passengers will be based on specific times, locations, and route segments.
- **Proactive Fleet Dispatching:** Surfaces forward-looking recommendations to operators and drivers, allowing them to allocate vehicles before demand peaks — eliminating reactive guessing and resource waste.

---

## Technical Architecture

The system is built to survive the constraints of real-world PUV deployment (unreliable power, low connectivity):

| Layer | Description |
|---|---|
| **Edge Inference** | An overhead camera feeds a continuous stream to the onboard device. YOLOv8-nano runs fully offline to detect passengers and update occupancy states, triggering the GPIO LED strip in real-time. |
| **Telemetry Sync** | The GPS and occupancy status are packaged into lightweight payloads and broadcast to a backend server. |
| **Cloud AI Processing** | The server processes telemetry against historical data to generate ETAs, detect route anomalies, log safety events, and run time-series demand forecasts. |
| **End-User Delivery** | Data is pushed out to the operator's dashboard (for proactive dispatching) and the commuter's low-bandwidth mobile interface (powering the AI chatbot recommendations). |

---

## Target Users

- **Daily Commuters:** Specifically, low-income passengers relying on all forms of transit, including traditional jeepneys, modern PUVs, buses, and UV express in urban and peri-urban areas.
- **Transport Operators and Dispatchers:** Requiring fleet oversight and demand forecasting, whether managing an informal local route or a modernized fleet.
- **Local Government Transport Authorities:** Requiring compliance data and traffic flow insights.

---

## Known Limitations

### Honest Assessment of Technical Risk

| Risk | Severity | Description |
|---|---|---|
| Operator Adoption | 🔴 HIGH | A social and political challenge, not a technical one. The platform requires GPS hardware installation and driver acceptance of occupancy monitoring. Without operator buy-in, there is no data — and without data, every AI component is inert. This is the single largest risk to real-world deployment. |
| GPS Signal Degradation | 🔴 HIGH | Covered terminals and tunnels cause GPS dropout at precisely the locations where commuters most need real-time information. Dead-reckoning using accelerometer data or cell-tower-based positioning must be considered as fallback mechanisms. |
| ETA Model Cold Start | 🟡 MEDIUM | Arrival prediction accuracy depends heavily on structured historical traffic data per route. In cities with no existing transit data infrastructure, the model starts cold. Cold-start predictions will be unreliable and must be communicated to users transparently. |
| Driver Tampering with GPS Hardware | 🟡 MEDIUM | Drivers who feel surveilled may disable or physically obstruct the GPS unit. The hardware mount must make tampering difficult and detectable. The server must distinguish between genuine signal loss and intentional disconnection. |
| Low-End Android Device Rendering | 🟢 LOW | Live map rendering on low-RAM Android devices is a known performance bottleneck. The commuter app must use tile-based static maps with minimal JavaScript rendering — not a full interactive map library. |

---

## Ethics & Safety Considerations

### Data Governance and Ethical Boundaries

- **Driver Privacy and Data Governance:** Driver location and behavior data must be governed by a clear, written policy: retained only for the operational period needed, not shared with third parties, and not used to penalize drivers without a formal due-process review. The system is advisory — it produces evidence for review, not automatic sanctions.
- **Alert Chain Integrity:** All safety anomaly alerts must route to operators and dispatchers first. Passengers are notified only after an operator has verified the event. Bypassing this chain risks panic at the passenger level and exposes drivers to unverified public accusations.
- **Commuter Location Data:** The commuter app must not store individual trip histories beyond the active session. Aggregate and anonymized demand data is acceptable for model training. Individual commuter movement profiles must never be retained or made accessible.
- **Fairness in Recommendations:** The commuter decision interface must not systematically disadvantage specific routes or operators through recommendation bias. Model outputs must be auditable by the relevant transport authority.
- **Accessibility as a Design Requirement:** The commuter app must function on low-cost Android devices with degraded network conditions. A system that only works on premium smartphones with strong data connections fails the exact population it is designed to serve.

---

## Why This Matters Now

While modern transit initiatives — such as the Philippine PUV Modernization Program — are pushing for updated fleets, millions of commuters still rely on traditional transport networks every single day. Advanced transit tech typically leaves legacy vehicles behind, but LoadSense is built for universal adaptability. As an inclusive, hardware-agnostic solution, it bridges the technological divide by easily retrofitting into both informal and modern PUVs with edge AI and affordable telematics, bringing smart-city safety and efficiency to the entire transport ecosystem and ensuring no commuter or driver is left behind.
