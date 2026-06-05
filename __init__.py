"""
HYPERION - Advanced Reasoning Amplification Engine
Transform any LLM into a super-intelligent reasoning system.

Example:
    >>> import asyncio
    >>> from hyperion import HyperionEngine, ModelRouter
    >>>
    >>> async def main():
    >>>     router = ModelRouter()
    >>>     engine = HyperionEngine(router=router)
    >>>     answer = await engine.solve("What is consciousness?")
    >>>     print(answer)
    >>>     await engine.aclose()
    >>>
    >>> asyncio.run(main())
"""

__version__ = "2.0.0"
__author__ = "Hyperion Contributors"
__license__ = "MIT"

from .core.hyperion import HyperionEngine
from .models.router import ModelRouter
from .models.async_backend import AsyncLLM
from .core.memory import MemoryStore
from .core.tools import ToolRegistry, Tool

__all__ = [
    "HyperionEngine",
    "ModelRouter",
    "AsyncLLM",
    "MemoryStore",
    "ToolRegistry",
    "Tool",
    "__version__",
]
