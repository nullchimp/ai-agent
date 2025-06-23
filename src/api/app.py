import os
from contextlib import asynccontextmanager
import mimetypes
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.routes import router, agent_instance, session_manager
mimetypes.add_type("application/javascript", ".js")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing agent and tools...")
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'mcp.json')
        await session_manager.discovery(config_path)
        for tool in session_manager.tools:
            agent_instance.add_tool(tool)
        print("Agent and tools initialized successfully.")
    except Exception as e:
        print(f"Error initializing MCP tools: {str(e)}")
    yield
    # Shutdown
    print("Shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Agent API",
        description="REST API for the AI Agent",
        version="1.0.0",
        lifespan=lifespan
    )

    app.include_router(router)

    static_files_path = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")
    if os.path.exists(static_files_path):
        app.mount(
            "/",
            StaticFiles(directory=static_files_path, html=True),
            name="static"
        )

    return app
