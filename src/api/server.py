import uvicorn
from api.app import create_app
from api.config.settings import api_settings

app = create_app()

def run_server() -> None:
    uvicorn.run(
        "api.app:create_app",
        host=api_settings.api_host,
        port=api_settings.api_port,
        factory=True,
        reload=api_settings.debug,
    )

if __name__ == "__main__":
    run_server()
