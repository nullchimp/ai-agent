import os
from contextlib import asynccontextmanager
from fastapi import FastAPI

from api.routes import router, agent, session_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Initializing agent and tools...")
    try:
        config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'mcp.json')
        await session_manager.discovery(config_path)
        for tool in session_manager.tools:
            agent.add_tool(tool)
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

    return app
