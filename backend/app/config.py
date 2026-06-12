import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    TMDB_API_KEY: Optional[str] = None
    
    # Server Settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def get_gemini_api_key(self) -> str:
        """Helper to get gemini API key from either GEMINI_API_KEY or GOOGLE_API_KEY."""
        key = self.GEMINI_API_KEY or self.GOOGLE_API_KEY or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not key:
            raise ValueError(
                "Gemini API key not found. Please set GEMINI_API_KEY or GOOGLE_API_KEY in your .env file."
            )
        return key

settings = Settings()
