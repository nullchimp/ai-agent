from pydantic_settings import BaseSettings
from typing import Optional

class APISettings(BaseSettings):
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["*"]
    
    class Config:
        env_prefix = "API_"
        case_sensitive = False

api_settings = APISettings()
