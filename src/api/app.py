from fastapi import FastAPI

from api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Agent API",
        description="REST API for the AI Agent",
        version="1.0.0"
    )
    
    app.include_router(router)
    
    return app
