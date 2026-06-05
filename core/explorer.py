import os
import re
from ..models.async_backend import AsyncLLM
from ..config import config


class MultiPathExplorer:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def explore(self, sub_problem: str, main_problem: str,
                      llm: AsyncLLM = None, use_cache: bool = True) -> list:
        llm = llm or self.llm
        num_paths = config.exploration_paths
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "explore.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{sub_problem}", sub_problem)\
                       .replace("{main_problem}", main_problem)\
                       .replace("{num_paths}", str(num_paths))

        messages = [
            {"role": "system", "content": f"You are a creative multi-path explorer. Generate exactly {num_paths} distinct approaches. Be concise but insightful."},
            {"role": "user", "content": prompt}
        ]
        result = await llm.chat(messages, temperature=0.8, use_cache=use_cache)
        paths = self._parse(result)

        if not paths:
            paths = [f"Direct analysis: {sub_problem[:100]}"]
        return paths[:max(num_paths, 1)]

    def _parse(self, result: str) -> list:
        paths = []
        lines = result.strip().split("\n")
        current = []
        path_markers = re.compile(r'^(Approach|Path|Option|Method|Strategy|Idea)\s*\d*\s*[:.]', re.I)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current:
                    paths.append(" ".join(current))
                    current = []
                continue

            if path_markers.match(stripped):
                if current:
                    paths.append(" ".join(current))
                text = re.sub(r'^.*?[:.]\s*', '', stripped, count=1) if (':' in stripped[:15] or '. ' in stripped[:10]) else stripped
                if len(text) < 10:
                    text = stripped
                current = [text]
            elif current:
                current.append(stripped)

        if current:
            paths.append(" ".join(current))

        if not paths:
            paragraphs = [p.strip() for p in result.split("\n\n") if len(p.strip()) > 50]
            paths = paragraphs[:3]
        return paths
