import os
import mimetypes
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import session_router, api_router

mimetypes.add_type("application/javascript", ".js")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Agent API",
        description="REST API for the AI Agent",
        version="1.0.0",
    )

    app.include_router(session_router)
    app.include_router(api_router)

    static_files_path = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")
    if os.path.exists(static_files_path):
        app.mount(
            "/",
            StaticFiles(directory=static_files_path, html=True),
            name="static"
        )

    return app
