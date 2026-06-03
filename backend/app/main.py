from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from .api.routes import router as api_router
from .core.config import config_value

app = FastAPI(title=config_value("project", "api_title", default="LoadSense Backend"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=config_value("server", "api_prefix", default="/api"))


@app.get("/health")
def health():
    return {"status": "ok"}


APP_DIR = Path(__file__).resolve().parents[2] / "app"
if APP_DIR.exists():
    app.mount("/", StaticFiles(directory=APP_DIR, html=True), name="loadsense_app")
