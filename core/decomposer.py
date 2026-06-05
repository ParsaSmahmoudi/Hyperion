import os
import re
from ..models.async_backend import AsyncLLM


class ProblemDecomposer:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def decompose(self, problem: str, llm: AsyncLLM = None, use_cache: bool = True) -> list:
        llm = llm or self.llm
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "decompose.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{problem}", problem)

        messages = [
            {"role": "system", "content": "You are a precise problem decomposition engine. Break the problem into exactly 3 clear, specific sub-problems. Follow the requested format exactly."},
            {"role": "user", "content": prompt}
        ]
        result = await llm.chat(messages, use_cache=use_cache)
        sub_problems = self._parse(result, problem)

        if not sub_problems or len(sub_problems) < 2:
            sub_problems = [
                f"Analyze the core components and first principles of: {problem}",
                f"Deep-dive into practical solutions and advanced aspects of: {problem}",
                f"Synthesize findings and verify conclusions about: {problem}"
            ]
        return sub_problems[:5]

    def _parse(self, result: str, original: str = "") -> list:
        lines = result.strip().split("\n")
        sub_problems = []
        pattern = re.compile(r'^(?:Sub-problem|Subproblem|Step|Phase)\s*\d+\s*[:.]\s*(.+)', re.I)

        for line in lines:
            m = pattern.match(line.strip())
            if m:
                text = m.group(1).strip()
                if text and len(text) > 15:
                    sub_problems.append(text)

        if not sub_problems:
            for line in lines:
                stripped = line.strip()
                if stripped and re.match(r'^\d+\s*[:.)]\s+', stripped):
                    text = re.sub(r'^\d+\s*[:.)]\s+', '', stripped)
                    if text and len(text) > 15:
                        sub_problems.append(text)

        return sub_problems
