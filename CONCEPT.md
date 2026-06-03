# TECHNICAL ROADMAP — USJR FlowerBoys ASEAN
> ASEAN AI Hackathon 2026 | Submission Deadline: May 17, 2026

---

## Team Information

| Field | Details |
|---|---|
| **Team Name** | USJR - FlowerBoys ASEAN |
| **Institution** | University of San Jose-Recoletos |
| **Country** | Philippines |
| **Track** | ✅ Smart Cities |
| **Team Leader** | Lejuene Delantar — lejuene.delantar.24@usjr.edu.ph — +639333210265 |

---

## Section 1: Executive Summary (Problem-Solution Fit)

Public transit in ASEAN cities — particularly Cebu, Philippines — operates with minimal real-time visibility on either side of the vehicle door. Commuters cannot determine a vehicle's occupancy before it arrives, nor predict arrival times. Drivers routinely exceed legal passenger capacity while operators lack demand data for efficient fleet allocation. Traffic congestion costs the Philippine economy PHP 3.5 billion daily in lost productivity, a crisis worsened by absent live monitoring that enables illegal overloading (*sabit*) and weakens safety compliance enforcement (JICA, 2018; LTFRB, 2024). In Cebu, commuters already report peak-period wait times exceeding 20 minutes, and existing transit technology consistently bypasses low-income passengers who depend on jeepneys most.

**LoadSense** is a dual-layer intelligent transportation platform designed to close this information gap.

- **Layer 1 — Edge AI (In-Vehicle):** An overhead camera runs YOLOv8-nano offline, performing bidirectional passenger counting and classifying occupancy into four tiers — 🟢 Green (available), 🟡 Yellow (filling), 🔴 Red (at capacity), and 🔴 Blinking Red (overloaded) — displayed via a windshield LED strip visible to waiting commuters.
- **Layer 2 — Cloud Intelligence:** GPS telemetry feeds a server that predicts arrival times, detects route deviations and driving anomalies, and forecasts demand.

Designed to retrofit into traditional jeepneys and modern PUVs without fleet replacement, LoadSense targets **SDG 9** and **SDG 11**.

---

## Section 2: Technical Architecture

### 2.1 System Components

| Inputs | Processing Core | Outputs |
|---|---|---|
| Overhead camera video stream (in-vehicle, continuous) | **Edge:** YOLOv8-nano (Offline) detects passengers; Telemetry Packager handles lightweight cellular transmission of state data to the cloud | LED strip color on windshield (Green / Yellow / Red / Blinking Red) |
| GPS coordinates from onboard hardware | **Cloud Server:** Gradient boosting ETA model; LSTM demand forecasting; route deviation and driving anomaly detection | ETA and occupancy on commuter mobile app |
| Historical occupancy logs and route records | **NLP Chatbot:** LLM API fusing occupancy + ETA for boarding recommendations | Fleet dispatching alerts on operator dashboard |
| Commuter natural-language queries (mobile app) | | Safety anomaly alerts (operators first, users after verification) |
| Live traffic and weather API feeds | | |

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LAYER 1 — INPUTS                                                        │
│  [GPS unit]          [Overhead Camera]        [Commuter queries]        │
│  Real-time position  Continuous video stream  NLP via mobile app        │
└──────────┬────────────────────┬──────────────────────────────────────────┘
           │ Coordinates        │ Video
┌──────────▼────────────────────▼──────────────────────────────────────────┐
│ LAYER 2 — EDGE                                                           │
│                                                                          │
│  [YOLOv8-nano inference]  ──GPIO──►  [LED state controller]             │
│  Raspberry Pi5 / Jetson Nano         Green/Yellow/Red/Blinking Red      │
│  Bidirectional line crossing counter                                     │
│  Receives updated weights ◄────────────────── (model update from cloud) │
│              │                                                           │
│  [Telemetry Packager]                                                    │
│  Lightweight broadcast: GPS + Occupancy State                            │
└──────────────┬───────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────────────┐
│ LAYER 3 — CLOUD                                                          │
│                                                                          │
│  [Traffic & Weather]    [FastAPI middleware]                             │
│  OpenWeatherMap API     routes + preprocesses telemetry                 │
│              │                    │                                      │
│  ┌───────────▼──────┐  ┌──────────▼──────────┐  ┌──────────────────┐  │
│  │ ETA prediction   │  │ Demand forecasting   │  │ Route & safety   │  │
│  │ Gradient boost   │  │ Prophet Hist. logs   │  │ monitor          │  │
│  └──────────────────┘  └──────────────────────┘  │ Deviation detect │  │
│                                                   │ Anomaly flagging │  │
│  Historical Data Retraining ◄──────────────────── └──────────────────┘  │
│                                                                          │
│  [Cloud Database]                                                        │
│  Historical logs · occupancy records · route data · model training store│
│              │                                                           │
│  [NLP Chatbot]                                                           │
│  LLM API · Boarding recommendation                                      │
└──────────────┬───────────────────────────────────────────────────────────┘
               │ Cloud Processing / Verified Operator Feedback
┌──────────────▼───────────────────────────────────────────────────────────┐
│ LAYER 4 — OUTPUT                                                         │
│                                                                          │
│  [Operator dashboard]     [Commuter app]    [Safety Alerts]             │
│  Fleet dispatching alerts Stop-level ETA   Anomaly flagging            │
│  Demand forecast view     Occupancy status  Operator-first verification │
│  Proactive reallocation   AI chatbot        before user notification    │
│  Incident log review      Map interface                                  │
│                                                                          │
│  [Physical LED unit]                                                     │
│  LED strip mounted above windshield · Direct commuter signal            │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Section 3: AI Approach & Model Selection

| Field | Details |
|---|---|
| **Primary AI Approach** | ✅ Machine Learning &nbsp; ✅ NLP &nbsp; ✅ Computer Vision |
| **Model Selection** | • **YOLOv8-nano** (Ultralytics/PyTorch) — offline edge passenger detection; deployed on Raspberry Pi 5 / Jetson Nano<br>• **Facebook Prophet** — server-side time-series demand forecasting from historical occupancy logs<br>• **Gradient Boosting Regressor (XGBoost)** — ETA prediction from GPS + traffic + weather features<br>• **LLM API** — lightweight cloud LLM for NLP boarding recommendation chatbot<br>• **Stack:** Python, C++, PyTorch, VS Code, FastAPI, React Native |
| **Reasoning** | YOLOv8-nano is the only YOLO variant deployable within the thermal envelope of an unattended edge device, achieving real-time inference without cloud dependency. Gradient boosting generalizes better than deep ETA models during cold-start phases. Facebook Prophet was explicitly selected over LSTM for demand forecasting because it handles missing data and irregular reporting intervals gracefully — crucial during early pilot phases with sparse telemetry. The LLM chatbot is API-based to prevent edge compute overhead. |

---

## Section 4: Data Strategy & Ethics

### Data Sources

| Source | Description |
|---|---|
| **Custom collection** | Overhead camera footage from pilot vehicles for YOLOv8 fine-tuning (collected under written operator consent) |
| **GPS telemetry** | Real-time position data from installed hardware |
| **Open-source** | OpenStreetMap (ODbL) for route geometry; MMDA/LTO historical traffic records for ETA model training |
| **Weather** | OpenWeatherMap API for ETA feature inputs |
| **System-generated** | Occupancy logs accumulated by LoadSense edge devices during pilot, bootstrapping the demand forecasting model |

### Data Quality & Cleaning

- GPS outliers removed via speed and heading sanity filters
- Camera frames with severe occlusion or insufficient lighting flagged and excluded from training sets
- Manual spot-check validation of occupancy counts during pilot phase
- ETA predictions annotated with explicit confidence bounds during cold-start period

### Licensing & Legality

- **OpenStreetMap:** ODbL permits use in this context.
- **OpenWeatherMap:** Standard API TOS permits use.
- **In-vehicle camera footage:** Collected under signed data collection agreements with vehicle operators. Footage is processed on-device; raw video is never transmitted or stored externally. Retained strictly for the pilot duration and deleted upon completion.
- **Custom GPS data:** Governed by written operator policy; no third-party sharing.

### Bias Mitigation & Fairness

- Training data collected across multiple routes, time-of-day windows, and vehicle types to prevent route-specific or temporal bias
- Occupancy classification is strictly threshold-based with no passenger profiling by appearance, demographics, or identity
- Commuter recommendations are auditable by the transport authority to detect systematic disadvantage to specific operators or routes
- Driver behavior data is advisory only; due-process review required before any disciplinary use — no automatic sanctions

---

## Section 5: Development Milestones (Agile Roadmap)

| Phase | Activity / Task | Tools Used | Expected Outcome |
|---|---|---|---|
| **Sprint 1** (May 1–15) | Camera test footage capture on pilot vehicle; dataset labeling for passenger detection; YOLOv8-nano environment setup and initial inference; GPS hardware integration and telemetry endpoint | Python, GitHub, Roboflow, Raspberry Pi / Jetson Nano, FastAPI | Labeled dataset; verified hardware; telemetry pipeline |
| **Sprint 2** (May 16–31) | Fine-tune YOLOv8-nano on custom passenger dataset; implement bidirectional line-crossing counter; GPIO LED strip integration for occupancy state output; GPS payload broadcast to backend server | VS Code, Ultralytics YOLOv8, PyTorch, FastAPI | Working edge AI occupancy counter; live GPS/occupancy broadcast |
| **Sprint 3** (June 1–15) | ETA model training (gradient boosting on GPS + traffic + weather); commuter mobile app UI with stop-level estimates; operator dashboard with fleet dispatching view; AI chatbot boarding recommendation interface | React Native, Figma, scikit-learn / XGBoost, FastAPI, LLM API | Working prototype: commuter app, operator dashboard, and chatbot |
| **Sprint 4** (June 16–25) | End-to-end integration testing; edge case debugging (GPS dropout, low-light detection); demand forecasting model validation; pitch preparation and demo video recording | GitKraken, Pytest, GitHub Actions | Final demo video; deployment-ready prototype |

---

## Section 6: Scalability & Regional Resilience

### Scaling Potential

LoadSense is hardware-agnostic, making ASEAN expansion a matter of procurement rather than architectural changes. Institutionally, initial scaling relies on partnering with local transport cooperatives under the LTFRB's PUV Modernization Program, positioning the system as a compliance-aligned add-on. Funding pathways include DOST-PCIEERD grants and smart city accelerator programs. The cloud layer scales horizontally, and cities with existing GTFS infrastructure can accelerate ETA training immediately. The commuter app targets low-RAM Android devices, the dominant device class across lower-income populations in Manila, Jakarta, and Ho Chi Minh City.

### Technical Constraints

| Risk Level | Constraint | Mitigation |
|---|---|---|
| 🔴 **HIGH** | **Operator Adoption** — Requires hardware installation and driver acceptance | Engage through existing PUV cooperatives; introduce a revenue-sharing model on aggregated demand data to create clear economic incentives for operators |
| 🔴 **HIGH** | **GPS Signal Degradation** — Covered terminals cause dropouts | Dead-reckoning via accelerometer or cell-tower fallback |
| 🟡 **MEDIUM** | **ETA Cold Start** — Prediction accuracy requires at least two weeks of accumulated operational data | Early estimates carry explicit uncertainty margins |
| 🟡 **MEDIUM** | **Driver Hardware Tampering** — Intentional hardware disconnection | Server flags disconnection as signal anomaly distinct from standard GPS dropout; physical mitigations to be finalized during pilot deployment |
| 🟢 **LOW** | **Mobile Rendering** — Full interactive maps are infeasible on low-RAM Android | Tile-based static maps used — a correct trade-off for the target user |

---

## References

- Codis, D. M. P. (2024, December 15). Cebuano commuters struggle with overcrowded public transport. *SunStar Cebu*. https://www.sunstar.com.ph/cebu/cebuano-commuters-struggle-with-overcrowded-public-transport
- Inquirer News. (2018, February 23). JICA: Traffic congestion now costs P3.5 billion a day. *Philippine Daily Inquirer*. https://newsinfo.inquirer.net/970553
- Inquirer Global Nation. (2026, January 6). Why PH commutes stay unreliable. *Inquirer.net*. https://globalnation.inquirer.net/304451/why-ph-commutes-stay-unreliable
- Land Transportation Franchising and Regulatory Board (LTFRB). (2024). *Guidelines on PUV overloading violations and penalties*. Republic of the Philippines.