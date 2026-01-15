from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_API_BASE: str

    # Tool
    CURRENCY_API_KEY: str


@lru_cache()
def get_api_settings() -> APISettings:
    return APISettings()
