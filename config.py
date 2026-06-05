import os

class Config:
    backend: str = "openrouter"
    api_key: str = os.getenv("HYPERION_API_KEY", "")
    base_url: str = os.getenv("HYPERION_BASE_URL", "https://openrouter.ai/api/v1")
    model: str = os.getenv("HYPERION_MODEL", "openrouter/auto")
    max_tokens: int = int(os.getenv("HYPERION_MAX_TOKENS", "16384"))
    temperature: float = 0.7
    reasoning_depth: int = int(os.getenv("HYPERION_REASONING_DEPTH", "2"))
    exploration_paths: int = int(os.getenv("HYPERION_EXPLORATION_PATHS", "2"))
    critic_rounds: int = int(os.getenv("HYPERION_CRITIC_ROUNDS", "1"))
    parallel: bool = os.getenv("HYPERION_PARALLEL", "true").lower() == "true"
    verbose: bool = True
    stream: bool = True

config = Config()
