from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import seed_if_needed
from routers import anomaly, chatbot, demand, eta, telemetry

seed_if_needed()

app = FastAPI(title="LoadSense API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(telemetry.router)
app.include_router(eta.router)
app.include_router(demand.router)
app.include_router(anomaly.router)
app.include_router(chatbot.router)


@app.get("/")
def root():
    return {"name": "LoadSense", "track": "ASEAN AI Hackathon 2026 Smart Cities", "ok": True}
