# src/models/chat_model.py
from langchain.chat_models import init_chat_model
from backend.src.config.settings import settings


def get_main_model(temperature: float = 0.7):
    """主力模型：用于推理和回答 (DeepSeek v4pro)"""
    return init_chat_model(
        model=f"openai:{settings.LLM_MODEL}",
        api_key=settings.LLM_API_KEY or None,
        base_url=settings.LLM_BASE_URL or None,
        temperature=temperature,
        max_tokens=8192,
    )


def get_mini_model(temperature: float = 0.3):
    """轻量模型：用于摘要、路由等辅助任务"""
    return init_chat_model(
        model=f"openai:{settings.LLM_MODEL_MINI}",
        api_key=settings.LLM_API_KEY or None,
        base_url=settings.LLM_BASE_URL or None,
        temperature=temperature,
        max_tokens=4096,
    )


# 使用示例
if __name__ == "__main__":
    model = get_main_model()
    print(f"主力模型: {model.model_name}")
    print(f"Base URL: {settings.LLM_BASE_URL}")
    print(f"支持函数调用: {model.profile.supports_function_calling}")
    print(f"支持结构化输出: {model.profile.supports_structured_output}")
