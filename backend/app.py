"""FastAPI application factory.

Mounts routes, serves static frontend files, configures CORS. Called by
uvicorn in production and by TestClient in tests.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes.execute import router as execute_router
from backend.routes.translate import router as translate_router

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def create_app() -> FastAPI:
    app = FastAPI(title="Hindi Python Playground")

    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"http://localhost(:\d+)?",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(translate_router)
    app.include_router(execute_router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

    return app
