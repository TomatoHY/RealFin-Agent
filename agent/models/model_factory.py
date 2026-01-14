from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel

from .api_settings import get_api_settings


MODEL_REGISTRY = {
    "gpt-3.5-turbo": {
        "class": ChatOpenAI,
        "real_name": "gpt-3.5-turbo-0613"
    },
    "gpt-4": {
        "class": ChatOpenAI,
        "real_name": "gpt-4-0613"
    },
    "claude-3-opus": {
        "class": ChatAnthropic,
        "real_name": "claude-3-opus-20240229"
    },
    "azure-gpt-4": {
        "class": AzureChatOpenAI,
        "real_name": "my-azure-deployment-name"  # Azure 通常填部署名
    }
}


def create_chat_model(model_name: str, **kwargs) -> BaseChatModel:
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
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            **kwargs
        )
    elif model_class == ChatAnthropic:
        return ChatAnthropic(
            model=real_name,
            anthropic_api_key=settings.anthropic_api_key,
            anthropic_api_base=settings.anthropic_api_base,
            **kwargs
        )
    elif model_class == AzureChatOpenAI:
        return AzureChatOpenAI(
            azure_deployment=real_name,
            openai_api_key=settings.azure_api_key,
            azure_endpoint=settings.azure_api_base,
            api_version=settings.azure_api_version,
            **kwargs
        )
    else:
        raise NotImplementedError(f"Factory for {model_class} is not implemented.")
