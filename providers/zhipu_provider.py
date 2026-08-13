"""Zhipu (GLM) provider."""

from __future__ import annotations

from providers.openai_compatible import OpenAICompatibleProvider


class ZhipuProvider(OpenAICompatibleProvider):
    name = "zhipu"
    base_url = "https://open.bigmodel.cn/api/paas/v4"
    default_model = "glm-4"
    api_key_env = "ZHIPU_API_KEY"
