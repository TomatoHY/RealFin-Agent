from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_openai import AzureChatOpenAI, ChatOpenAI

import logging
from ..utils import get_api_settings


MODEL_REGISTRY = {
    # OpenAI 系列
    "gpt-5.1": {
        "class": ChatOpenAI,
        "real_name": "gpt-5.1"
    },
    "gpt-5.2": {
        "class": ChatOpenAI,
        "real_name": "gpt-5.2"
    },
    # Anthropic/Claude 系列
    "claude-haiku-4.5": {
        "class": ChatOpenAI,
        "real_name": "claude-haiku-4-5-20251001"
    },
    "claude-sonnet-4.5": {
        "class": ChatOpenAI,
        "real_name": "claude-sonnet-4-5-20250929"
    },
    "claude-opus-4.5": {
        "class": ChatOpenAI,
        "real_name": "claude-opus-4-5-20251101"
    },
    "claude-sonnet-4.6": {
        "class": ChatOpenAI,
        "real_name": "claude-sonnet-4-6"
    },
    "claude-opus-4.6": {
        "class": ChatOpenAI,
        "real_name": "claude-opus-4-6"
    },
    # DeepSeek 系列
    "deepseek-v3.2": {
        "class": ChatOpenAI,
        "real_name": "deepseek-v3.2"
    },
    # Kimi 系列
    "kimi-k2": {
        "class": ChatOpenAI,
        "real_name": "Kimi-K2"
    },
    # Qwen via RealFin
    "qwen3-max": {
        "class": ChatOpenAI,
        "real_name": "qwen/qwen3-max"
    },
}


def create_chat_model(model_name: str, location: str = "realfin", **kwargs) -> BaseChatModel:
    model_name = model_name.lower()
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model name: {model_name}. "
                         f"Available models: {list(MODEL_REGISTRY.keys())}")
    config = MODEL_REGISTRY[model_name]
    model_class = config["class"]
    real_name = config["real_name"]
    settings = get_api_settings()

    if model_class == ChatOpenAI:
        if location == "realfin":
            api_key = settings.REALFIN_API_KEY
            api_base = settings.REALFIN_API_BASE
        else:
            api_key = settings.OPENAI_API_KEY
            api_base = settings.OPENAI_API_BASE
        return ChatOpenAI(
            model=real_name,
            openai_api_key=api_key,
            openai_api_base=api_base,
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
