import os
import re
from ..models.async_backend import AsyncLLM


class Verifier:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def verify(self, problem: str, answer: str,
                     llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "verify.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{problem}", problem)\
                       .replace("{answer}", answer)

        messages = [
            {"role": "system", "content": "You are a strict QA engineer. Verify answers and ALWAYS return the complete final answer after VERIFIED or CORRECTED."},
            {"role": "user", "content": prompt}
        ]
        result = await llm.chat(messages, use_cache=use_cache)
        return self._extract(result, answer)

    def _extract(self, result: str, default: str) -> str:
        lines = result.strip().split("\n")
        corr_idx = -1
        ver_idx = -1
        for i, line in enumerate(lines):
            if line.strip().upper().startswith("CORRECTED"):
                corr_idx = i
            if line.strip().upper().startswith("VERIFIED"):
                ver_idx = i

        if corr_idx >= 0:
            corr_text = "\n".join(l.strip() for l in lines[corr_idx + 1:] if l.strip())
            if corr_text:
                return corr_text
        if ver_idx >= 0:
            ver_text = "\n".join(l.strip() for l in lines[ver_idx + 1:] if l.strip())
            if ver_text:
                return ver_text
        return default
