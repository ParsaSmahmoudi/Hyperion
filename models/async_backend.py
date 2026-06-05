"""
Async LLM backend with HTTP/2, connection pooling, and built-in caching.
Supports OpenAI-compatible APIs (OpenAI, OpenRouter, Ollama, etc.)
"""
import json
import os
import asyncio
import hashlib
import time
from typing import Optional, List, Dict, Any
import httpx
import diskcache
from ..config import config

_SSL_VERIFY = os.getenv("HYPERION_SSL_VERIFY", "false").lower() == "true"
_CACHE_DIR = os.path.expanduser(os.getenv("HYPERION_CACHE_DIR", "~/.hyperion_cache"))
_CACHE_TTL = int(os.getenv("HYPERION_CACHE_TTL", "86400"))  # 24 hours

_cache: Optional[diskcache.Cache] = None


def get_cache() -> diskcache.Cache:
    global _cache
    if _cache is None:
        os.makedirs(_CACHE_DIR, exist_ok=True)
        _cache = diskcache.Cache(_CACHE_DIR, size_limit=int(1e9))
    return _cache


def _cache_key(messages: List[Dict], model: str, temperature: float, max_tokens: int) -> str:
    raw = json.dumps({"m": messages, "model": model, "t": temperature, "mt": max_tokens}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(raw.encode()).hexdigest()


class AsyncLLM:
    """Async LLM client with connection pooling, retries, and caching"""

    def __init__(self, backend: str = None, api_key: str = None, model: str = None,
                 base_url: str = None, max_concurrent: int = 8):
        self.backend = backend or config.backend
        self.api_key = api_key or config.api_key
        self.model = model or config.model
        self.base_url = base_url or config.base_url
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            limits = httpx.Limits(max_connections=20, max_keepalive_connections=10)
            self._client = httpx.AsyncClient(
                verify=_SSL_VERIFY,
                limits=limits,
                timeout=httpx.Timeout(30, read=300),
                http2=False
            )
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _call_openai(self, messages: List[Dict], temperature: float = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if self.backend == "openrouter":
            headers["HTTP-Referer"] = "https://github.com/trainllm/hyperion"
            headers["X-Title"] = "Hyperion"

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": temperature or config.temperature,
        }

        client = await self._get_client()

        async with self._semaphore:
            for attempt in range(3):
                try:
                    resp = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )
                    if resp.status_code == 402:
                        raise Exception("API_CREDIT_LIMIT")
                    resp.raise_for_status()
                    return resp.json()["choices"][0]["message"]["content"]
                except (httpx.TimeoutException, httpx.ConnectError) as e:
                    if attempt < 2:
                        await asyncio.sleep(2 * (attempt + 1))
                        continue
                    raise

    async def _call_ollama(self, messages: List[Dict], temperature: float = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "num_predict": config.max_tokens,
                "temperature": temperature or config.temperature,
            }
        }

        client = await self._get_client()
        async with self._semaphore:
            resp = await client.post(f"{self.base_url}/api/chat", json=payload)
            resp.raise_for_status()
            data = resp.json()
            if "message" in data:
                return data["message"]["content"]
            return data.get("response", "")

    async def chat(self, messages: List[Dict], temperature: float = None,
                   use_cache: bool = True, cache_ttl: int = None) -> str:
        if use_cache:
            cache = get_cache()
            key = _cache_key(messages, self.model, temperature or config.temperature, config.max_tokens)
            cached = cache.get(key)
            if cached is not None:
                return cached

        if self.backend == "ollama":
            result = await self._call_ollama(messages, temperature)
        else:
            result = await self._call_openai(messages, temperature)

        if use_cache:
            cache.set(key, result, expire=cache_ttl or _CACHE_TTL)

        return result

    async def chat_stream(self, messages: List[Dict], temperature: float = None):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": temperature or config.temperature,
            "stream": True
        }

        client = await self._get_client()
        async with self._semaphore:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            if "content" in delta:
                                yield delta["content"]
                        except json.JSONDecodeError:
                            continue

    def chat_sync(self, messages: List[Dict], temperature: float = None) -> str:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as ex:
                    return ex.submit(asyncio.run, self.chat(messages, temperature)).result()
            else:
                return loop.run_until_complete(self.chat(messages, temperature))
        except RuntimeError:
            return asyncio.run(self.chat(messages, temperature))
