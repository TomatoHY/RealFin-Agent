from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # OpenAI (optional, used when location=openai)
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""

    # RealFin proxy (used when location=realfin)
    REALFIN_API_KEY: str = ""
    REALFIN_API_BASE: str = "http://113.45.39.247:3001/v1"

    # Tool
    CURRENCY_API_KEY: str = ""


@lru_cache()
def get_api_settings() -> APISettings:
    return APISettings()
