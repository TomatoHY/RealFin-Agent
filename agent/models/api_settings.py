from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class ModelAPISettings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_BASE_URL: str
    OPENAI_MODEL_NAME: str


@lru_cache()
def get_api_settings() -> ModelAPISettings:
    return ModelAPISettings()
