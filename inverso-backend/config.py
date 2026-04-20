from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    ANTHROPIC_API_KEY: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    NEWS_API_KEY: str = ""
    SECRET_KEY: str = "cambiar-en-produccion"
    ENVIRONMENT: str = "development"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
