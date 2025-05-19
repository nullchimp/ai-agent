from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import agent_routes

def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Agent API",
        description="REST API for the AI Agent system",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.include_router(agent_routes.router)
    
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        return {"status": "healthy"}
    
    return app
