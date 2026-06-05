"""
Tool use system for Hyperion.
Provides calculator, web search, code execution, file I/O, and more.
"""
import os
import sys
import math
import json
import re
import subprocess
import tempfile
import urllib.parse
from typing import List, Dict, Any, Optional
import asyncio
import httpx


class Tool:
    """Base class for all tools"""
    name: str = ""
    description: str = ""
    parameters: Dict[str, str] = {}

    def run(self, **kwargs) -> str:
        raise NotImplementedError

    def schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }


class CalculatorTool(Tool):
    name = "calculator"
    description = "Perform mathematical calculations. Input: a Python math expression."
    parameters = {"expression": "A math expression like '2+2' or 'sqrt(144)'"}

    def run(self, expression: str) -> str:
        try:
            safe_dict = {
                "__builtins__": {},
                "abs": abs, "round": round, "min": min, "max": max,
                "sum": sum, "pow": pow,
                **{k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
            }
            result = eval(expression, safe_dict)
            return f"Result: {result}"
        except Exception as e:
            return f"Error: {e}"


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web for information. Input: a search query string."
    parameters = {"query": "The search query"}

    async def arun(self, query: str) -> str:
        try:
            url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1"
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                data = resp.json()
                if data.get("AbstractText"):
                    return f"Abstract: {data['AbstractText']}\nSource: {data.get('AbstractSource', '')}"
                related = data.get("RelatedTopics", [])
                if related:
                    return "\n".join([f"- {r.get('Text', '')[:200]}" for r in related[:5] if r.get("Text")])
                return f"No results found for: {query}"
        except Exception as e:
            return f"Search error: {e}"

    def run(self, query: str) -> str:
        return asyncio.run(self.arun(query))


class CodeExecTool(Tool):
    name = "code_exec"
    description = "Execute Python code in a sandboxed subprocess. Input: Python code."
    parameters = {"code": "Python code to execute"}

    def run(self, code: str) -> str:
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as f:
                f.write(code)
                tmp_path = f.name
            try:
                result = subprocess.run(
                    [sys.executable, tmp_path],
                    capture_output=True, text=True, timeout=10,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"}
                )
                output = result.stdout
                if result.stderr:
                    output += f"\n[STDERR]: {result.stderr}"
                if result.returncode != 0:
                    output += f"\n[EXIT CODE: {result.returncode}]"
                return output[:2000] or "[no output]"
            finally:
                os.unlink(tmp_path)
        except subprocess.TimeoutExpired:
            return "Error: execution timed out (10s limit)"
        except Exception as e:
            return f"Error: {e}"


class FileReadTool(Tool):
    name = "read_file"
    description = "Read the contents of a file. Input: file path."
    parameters = {"path": "Path to the file"}

    def run(self, path: str) -> str:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()[:3000]
        except Exception as e:
            return f"Error: {e}"


class CurrentTimeTool(Tool):
    name = "current_time"
    description = "Get the current date and time."
    parameters = {}

    def run(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ToolRegistry:
    """Registry of all available tools"""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_defaults()

    def _register_defaults(self):
        for tool in [CalculatorTool(), WebSearchTool(), CodeExecTool(),
                     FileReadTool(), CurrentTimeTool()]:
            self.register(tool)

    def register(self, tool: Tool):
        self.tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def describe(self) -> str:
        out = "Available tools:\n"
        for name, tool in self.tools.items():
            out += f"  • {name}: {tool.description}\n"
        return out

    async def use(self, name: str, **kwargs) -> str:
        tool = self.get(name)
        if not tool:
            return f"Error: tool '{name}' not found"
        if hasattr(tool, "arun"):
            return await tool.arun(**kwargs)
        return tool.run(**kwargs)


def extract_tool_calls(text: str) -> List[Dict]:
    """Extract tool calls from LLM output like: USE_TOOL[calculator] expr = 2+2"""
    calls = []
    pattern = r'USE_TOOL\[(\w+)\](.*?)(?=USE_TOOL\[|\Z)'
    for match in re.finditer(pattern, text, re.DOTALL):
        tool_name = match.group(1)
        rest = match.group(2).strip()
        kwargs = {}
        for line in rest.split("\n"):
            if "=" in line:
                k, v = line.split("=", 1)
                kwargs[k.strip()] = v.strip()
        calls.append({"tool": tool_name, "kwargs": kwargs})
    return calls


async def execute_tool_calls(text: str, registry: ToolRegistry) -> str:
    """Execute any tool calls found in text"""
    calls = extract_tool_calls(text)
    if not calls:
        return ""
    results = []
    for call in calls:
        result = await registry.use(call["tool"], **call["kwargs"])
        results.append(f"Tool [{call['tool']}]: {result}")
    return "\n".join(results)
