import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "fAIshion - AI-Powered Wardrobe Assistant"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/fashiondb")
    
    # You can add other API keys and settings here

    class Config:
        env_file = ".env"

settings = Settings()
