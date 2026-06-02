from fastapi import FastAPI
from .api.routes import router as api_router

app = FastAPI(title="LoadSense Backend")

app.include_router(api_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
