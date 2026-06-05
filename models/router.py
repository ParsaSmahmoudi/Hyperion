"""
Multi-model router for Hyperion.
Uses different models for different reasoning layers:
- Fast model: exploration, search, decomposition
- Strong model: synthesis, verification, final answer
"""
import os
from typing import Optional, Dict
from ..config import config
from .async_backend import AsyncLLM


# Recommended model tiers
FAST_MODELS = {
    "openrouter": ["openrouter/auto", "openai/gpt-4o-mini", "google/gemini-flash-1.5"],
    "openai": ["gpt-4o-mini", "gpt-3.5-turbo"],
    "ollama": ["llama3.1:8b", "qwen2.5:7b", "mistral:7b"],
}

STRONG_MODELS = {
    "openrouter": ["openai/gpt-4o", "anthropic/claude-3.5-sonnet", "google/gemini-pro-1.5"],
    "openai": ["gpt-4o", "gpt-4-turbo", "o1-preview"],
    "ollama": ["llama3.1:70b", "qwen2.5:32b", "mixtral:8x22b"],
}


class ModelRouter:
    """Routes different reasoning tasks to different models"""

    def __init__(self, backend: str = None, api_key: str = None, base_url: str = None,
                 fast_model: str = None, strong_model: str = None):
        self.backend = backend or config.backend
        self.api_key = api_key or config.api_key
        self.base_url = base_url or config.base_url
        self.fast_model = fast_model or os.getenv("HYPERION_FAST_MODEL", FAST_MODELS.get(self.backend, ["openrouter/auto"])[0])
        self.strong_model = strong_model or os.getenv("HYPERION_STRONG_MODEL", STRONG_MODELS.get(self.backend, ["openrouter/auto"])[0])
        self._cache: Dict[str, AsyncLLM] = {}

    def get(self, model_name: str = None) -> AsyncLLM:
        if model_name is None:
            model_name = self.fast_model
        if model_name not in self._cache:
            self._cache[model_name] = AsyncLLM(
                backend=self.backend,
                api_key=self.api_key,
                model=model_name,
                base_url=self.base_url
            )
        return self._cache[model_name]

    def fast(self) -> AsyncLLM:
        return self.get(self.fast_model)

    def strong(self) -> AsyncLLM:
        return self.get(self.strong_model)

    async def aclose(self):
        for llm in self._cache.values():
            await llm.aclose()
        self._cache.clear()
