from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import AzureChatOpenAI, ChatOpenAI

import logging
from ..utils import get_api_settings


MODEL_REGISTRY = {
    "claude-haiku-4.5": {
        "class": ChatOpenAI,
        "real_name": "anthropic/claude-haiku-4.5"
    },
    "claude-sonnet-4.5": {
        "class": ChatOpenAI,
        "real_name": "anthropic/claude-sonnet-4.5"
    },
    "deepseek-v3.2": {
        "class": ChatOpenAI,
        "real_name": "deepseek/deepseek-v3.2"
    },
    "gpt-5-chat": {
        "class": ChatOpenAI,
        "real_name": "openai/gpt-5-chat"
    },
    "gpt-5.1": {
        "class": ChatOpenAI,
        "real_name": "openai/gpt-5.1"
    },
    "gemini-3-pro-preview": {
        "class": ChatOpenAI,
        "real_name": "google/gemini-3-pro-preview"
    },
    "kimi-k2": {
        "class": ChatOpenAI,
        "real_name": "Kimi-K2"
    }
}


def create_chat_model(model_name: str, **kwargs) -> BaseChatModel:
    model_name = model_name.lower()
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model name: {model_name}. "
                         f"Available models: {list(MODEL_REGISTRY.keys())}")
    config = MODEL_REGISTRY[model_name]
    model_class = config["class"]
    real_name = config["real_name"]
    settings = get_api_settings()

    if model_class == ChatOpenAI:
        return ChatOpenAI(
            model=real_name,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            **kwargs
        )
    # elif model_class == ChatAnthropic:
    #     return ChatAnthropic(
    #         model=real_name,
    #         anthropic_api_key=settings.ANTHROPIC_API_KEY,
    #         anthropic_api_base=settings.ANTHROPIC_API_BASE,
    #         **kwargs
    #     )
    # elif model_class == AzureChatOpenAI:
    #     return AzureChatOpenAI(
    #         azure_deployment=real_name,
    #         openai_api_key=settings.AZURE_API_KEY,
    #         azure_endpoint=settings.AZURE_API_BASE,
    #         api_version=settings.AZURE_API_VERSION,
    #         **kwargs
    #     )
