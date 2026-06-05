import os
import re
from ..models.async_backend import AsyncLLM
from ..config import config


class SelfCritic:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def critique(self, sub_problem: str, solution: str,
                       llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        max_rounds = config.critic_rounds
        current = solution

        for r in range(1, max_rounds + 1):
            prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "critique.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
            prompt = template.replace("{sub_problem}", sub_problem)\
                           .replace("{solution}", current)\
                           .replace("{round}", str(r))\
                           .replace("{max_rounds}", str(max_rounds))
            messages = [
                {"role": "system", "content": "You are a ruthless but constructive critic. Find every flaw and provide the complete improved solution."},
                {"role": "user", "content": prompt}
            ]
            result = await llm.chat(messages, use_cache=use_cache)
            extracted = self._extract(result)
            if extracted:
                current = extracted

        return current

    def _extract(self, text: str) -> str:
        m = re.search(r'(?:IMPROVED SOLUTION|Improved Solution|Improved solution|CORRECTED|Corrected)[:\s]*\n*(.*?)$', text, re.DOTALL)
        if m:
            return m.group(1).strip()
        return ""
