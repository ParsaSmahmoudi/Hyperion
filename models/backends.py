import json
import requests
import os
import time
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional
from ..config import config

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_SSL_VERIFY = os.getenv("HYPERION_SSL_VERIFY", "false").lower() == "true"


def _make_session():
    session = requests.Session()
    retry_strategy = Retry(
        total=3,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["POST"]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=4, pool_maxsize=8)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class LLMBackend:
    def __init__(self, backend: str = None, api_key: str = None, model: str = None, base_url: str = None):
        self.backend = backend or config.backend
        self.api_key = api_key or config.api_key
        self.model = model or config.model
        self.base_url = base_url or config.base_url
        self._session = _make_session()

    def _request_kwargs(self):
        return {"verify": _SSL_VERIFY, "timeout": (30, 300)}

    def _call_openai(self, messages: list, temperature: float = None) -> str:
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

        kw = self._request_kwargs()
        for attempt in range(2):
            try:
                resp = self._session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers, json=payload, **kw
                )
                if resp.status_code == 402:
                    raise Exception("API_CREDIT_LIMIT: OpenRouter API key has insufficient credits")
                resp.raise_for_status()
                return resp.json()["choices"][0]["message"]["content"]
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == 0:
                    time.sleep(3)
                    self._session = _make_session()
                    continue
                raise

    def _call_ollama(self, messages: list, temperature: float = None) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "options": {
                "num_predict": config.max_tokens,
                "temperature": temperature or config.temperature,
            }
        }
        kw = self._request_kwargs()
        resp = self._session.post(
            f"{self.base_url}/api/chat", json=payload, **kw
        )
        resp.raise_for_status()
        data = resp.json()
        if "message" in data:
            return data["message"]["content"]
        return data.get("response", "")

    def chat(self, messages: list, temperature: float = None) -> str:
        if self.backend == "ollama":
            return self._call_ollama(messages, temperature)
        return self._call_openai(messages, temperature)

    def chat_stream(self, messages: list, temperature: float = None):
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
            "stream": True
        }

        kw = self._request_kwargs()
        kw["stream"] = True
        with self._session.post(
            f"{self.base_url}/chat/completions",
            headers=headers, json=payload, **kw
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if line:
                    line = line.decode("utf-8")
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
