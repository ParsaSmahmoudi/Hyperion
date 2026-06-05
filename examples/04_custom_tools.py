"""
Example 4: Custom tool
Add your own custom tools to the registry.
"""
import asyncio
import os
os.environ.setdefault("HYPERION_SSL_VERIFY", "false")
os.environ.setdefault("HYPERION_API_KEY", "your-api-key-here")

from hyperion.core.hyperion import HyperionEngine
from hyperion.core.tools import ToolRegistry, Tool
from hyperion.models.router import ModelRouter


class WeatherTool(Tool):
    name = "weather"
    description = "Get current weather for a city. Input: city name."
    parameters = {"city": "City name"}

    def run(self, city: str) -> str:
        # In a real app, call a weather API
        return f"Weather in {city}: 72°F, sunny (mock data)"


class StockTool(Tool):
    name = "stock"
    description = "Get stock price. Input: stock ticker symbol."
    parameters = {"ticker": "Stock ticker (e.g. AAPL)"}

    def run(self, ticker: str) -> str:
        return f"{ticker} stock price: $150.00 (mock data)"


async def main():
    router = ModelRouter()
    tools = ToolRegistry()
    tools.register(WeatherTool())
    tools.register(StockTool())

    engine = HyperionEngine(router=router, tools=tools, verbose=True)
    answer = await engine.solve(
        "What's the weather in Tokyo and what's the current AAPL stock price?"
    )
    print(f"\n=== ANSWER ===\n{answer}")
    await engine.aclose()


if __name__ == "__main__":
    asyncio.run(main())
