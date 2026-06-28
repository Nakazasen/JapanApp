"""Configuration management."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Reload .env file to ensure latest settings
load_dotenv(override=True)


class Settings(BaseSettings):
    """Application settings."""
    
    # Paths
    project_root: str = os.getenv("PROJECT_ROOT", r"C:\ProgramData\Sandbox\Projects\EnglishApp")
    # Database
    db_path: str = os.getenv("DB_PATH", r"C:\ProgramData\Sandbox\Projects\EnglishApp\db\app.db")
    
    # Backend
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # API Keys
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    
    # NOTE: Gemini models are now managed dynamically via ai_settings.json
    # See: backend/services/ai_service.py -> AIConfigManager


    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Bỏ qua các biến không được khai báo trong model


# Global settings instance
settings = Settings()

# Ensure directories exist
Path(settings.project_root).mkdir(parents=True, exist_ok=True)
Path(os.path.dirname(settings.db_path)).mkdir(parents=True, exist_ok=True)

