from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    NEWS_API_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    SECRET_KEY: str = "cambiar-en-produccion"
    ENVIRONMENT: str = "development"
    IOL_USERNAME: str = ""
    IOL_PASSWORD: str = ""

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
