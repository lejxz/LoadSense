# 🎬 LoadSense — 5-Minute Pitch Video Script
### Team FlowerBoys · USJR · ASEAN AI Hackathon 2026

> **Format:** Animated PowerPoint presentation / Video Script.  
> **Style:** Pictures/illustrations animated ppt slides, side-by-side demo video layout for solution section.  

---

## ⏱️ Timing Overview

| Section | Duration | Cumulative |
|---|---|---|
| 1. Hook (LED Strip Logic) | 0:20 | 0:20 |
| 2. Team & Product Introduction | 0:20 | 0:40 |
| 3. Problem & Differentiation | 0:45 | 1:25 |
| 4. Target Segments | 0:15 | 1:40 |
| 5. Solution: The AI Workflow & Demo | 1:50 | 3:30 |
| 6. Business Model & Costing | 0:45 | 4:15 |
| 7. Closing / Call to Action | 0:45 | 5:00 |

---

## 🎬 SECTION 1 — Hook (0:20)

**Visuals:**
- Black screen then Slide 1 fades in along with the voice-over.
- **Slide 1:** Picture of a student (**Kent**) waiting at a designated stop. A jeepney approaches with a **Red LED strip** glowing brightly on its dashboard.
- **Slide 2:** The jeepney drives past because it's full. Kent looks sad and frustrated. Clock ticks.
- **Slide 3:** *Rewind effect!* Back to the stop. A different jeepney approaches, this time with a **Green LED strip**.
- **Slide 4:** Kent smiles, waves it down, and easily boards the jeepney. 

**Voice-over (Kent):**
> *"Every day, thousands of students wait at jeepney stops, guessing if the next ride has space. Jeepney comes, red LED? It's full. You're left sad and late. But what if the jeepney arrives with a green LED? You know there's a seat for you. You board, you're happy, you're on time. With LoadSense, we take the guesswork out of commuting."*

**Transition:** LoadSense logo animation.

---

## 🎬 SECTION 2 — Team & Product Introduction (0:20) 

**Visuals:**
- Team name card: **"Team FlowerBoys"** with USJR branding.
- LoadSense logo animates in with the tagline.

**Voice-over (Perejan):**
> *"We are Team FlowerBoys from the University of San Jose–Recoletos, Cebu. And we are proud to introduce **LoadSense** — an intelligent transportation platform that brings Edge AI and real-time transit intelligence to every PUV on the road."*

---

## 🎬 SECTION 3 — Problem & Differentiation (0:45)

**Visuals (animated infographic slides):**
- Map of Cebu with congested route indicators pulsing red.
- Stat card animate-in: **"₱3.5 Billion lost daily"** to traffic congestion.
- App comparison visual: Google Maps logo vs. LoadSense logo. Google Maps shows a route line; LoadSense shows the route line *plus* live jeepney capacity bubbles.

**Voice-over (Kent):**
> *"The Philippine public transport system lacks visibility. Commuters don't know if a jeepney is minutes away, or if it's already full. You might ask, 'Why not just use Google Maps or standard transit apps?' While Google Maps is great for static routes and traffic estimations, it has **zero real-time capacity awareness** for informal transit like jeepneys. It doesn't know if the jeep is packed or empty.*
> *LoadSense bridges this exact data gap. We don't just tell you where the jeepney is; we tell you if you can actually fit inside it."*

---

## 🎬 SECTION 4 — Target Segments (0:15)

**Visuals:** Three animated cards appear side by side.

| 👤 Commuters | 🚌 PUV Operators | 🏛️ Government / LGUs |
|---|---|---|
| Need real-time ride info | Need fleet oversight tools | Need compliance data & enforcement |

**Voice-over (Perejan):**
> *"LoadSense serves three groups: **commuters** needing live ride info, **PUV cooperatives** needing fleet management, and **LGUs** needing data-driven transport compliance."*

---

## 🎬 SECTION 5 — Solution: The AI Workflow & Demo (1:50)

### 5A — The AI Workflow under the hood (0:40)

**[Kent]**
**Visual:** 3D or schematic diagram of a jeepney interior. Highlights an Overhead Camera connected to a Raspberry Pi/Jetson Nano. Arrows point to the external LED strip and up to a Cloud Database. Snippets of YOLO bounding boxes detecting people.

> *"Because this is an AI hackathon, let's look at our engine. How do we know the occupancy? We use **Edge AI**. Inside the jeepney, an overhead camera connects to an edge device like a Raspberry Pi 5 or Jetson Nano. We run a lightweight computer vision model—specifically object detection like YOLO—to track passengers crossing the door threshold. All processing happens locally on the edge. This means it's fast, works without internet for the LED logic, and preserves privacy since no video is sent to the cloud. The AI simply outputs a passenger count, updates the Green or Red LED strip outside, and pushes a lightweight data payload to our cloud via a GPS module."*

---

### 5B — User / Mobile App (0:35)

**[Perejan]**
**Visual 1:** App screen showing live map with color-coded jeepneys (🟢🟡🔴).
**Visual 2:** AI chatbot screen. User types: *"Which PUV should I take to reach SM City?"* → Response appears with route name, occupancy, and ETA.

> *"For the commuter, all this AI translates to a seamless app experience. Open LoadSense and instantly see every PUV on your route—color-coded Green, Yellow, or Red. Plus, we've integrated an **AI Chatbot Assistant**. Just ask in plain text, 'How do I get to SM City?' and the AI reads the live fleet data to tell you exactly which PUV to board, its current capacity, and ETA."*

---

### 5C — Operator Dashboard (0:35)

**[Kent]**
**Visual:** Operator Dashboard screen showing a demand forecasting chart and an overloading alert panel.

> *"For the operators, the data is transformed into predictive analytics. LoadSense uses historical data to forecast passenger demand, allowing operators to pre-position vehicles before the rush hour hits. Furthermore, if the Edge AI detects illegal overloading, an automated alert is flagged on the operator's dashboard for immediate review and action."*

---

## 🎬 SECTION 6 — Business Model & Costing (0:45)

**Visuals:** Animated Cost Breakdown & Pricing table showing three tiers (Co-op, LGU, Enterprise API). B2G2B flow diagram.

**Voice-over (Perejan):**
> *"Our hardware is a one-time, retrofit-ready cost of roughly **₱11,000 per vehicle** (under $200). But LoadSense scales as a software company. We have three recurring revenue streams:*
> 
> *First, we charge PUV cooperatives a **₱500 monthly SaaS fee per vehicle** for fleet tracking and predictive demand analytics.*
> 
> *Second, we offer LGUs a **Smart City Compliance Dashboard for ₱50,000 a month**, giving the government instant visibility on city-wide traffic flow and illegal overloading.*
> 
> *Finally, we monetize our raw data. We provide an **Enterprise API** for third-party apps—like Sakay.ph, Google Maps, or real estate platforms—at **₱10,000 per month**, allowing them to integrate live jeepney availability into their own services. Hardware gets us on the road, but data is our true business."*

---

## 🎬 SECTION 7 — Closing / Call to Action (0:45)

**Visuals:**
- LTFRB PUV Modernization Program + news headlines visual.
- Final slide: LoadSense logo + tagline + QR code(full demo video) + contact.

**Voice-over (both, alternating lines):**

> **Perejan:** *"The LTFRB's PUV Modernization Program is mandating that jeepneys be upgraded. Operators are desperately looking for affordable technology that helps them comply and survive."*

> **Kent:** *"LoadSense is built for this moment. We are retrofit-ready, hardware-agnostic, and driven by accessible Edge AI. We work on the PUVs that are on the road right now."*

> **Perejan:** *"Real information. Safer rides. Smarter cities."*

> **Kent:** *"This is LoadSense. Thank you."*

---

## 📝  Notes

| Element | Recommendation |
|---|---|
| **Transition music** | Low, tense ambient for hook → upbeat, clean tech music from Section 2 onward |
| **Stat sources** | Cite on-slide in small text |
