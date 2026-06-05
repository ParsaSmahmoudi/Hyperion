import os
from ..models.async_backend import AsyncLLM


class Synthesizer:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def synthesize(self, main_problem: str, solutions: list,
                        llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        solutions_text = ""
        for i, sol in enumerate(solutions, 1):
            solutions_text += f"\n--- SOLUTION {i} ---\n{sol}\n"

        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "synthesize.txt")
        with open(prompt_path, "r", encoding="utf-8") as f:
            template = f.read()
        prompt = template.replace("{main_problem}", main_problem)\
                       .replace("{solutions}", solutions_text)

        messages = [
            {"role": "system", "content": "You are a master synthesizer who combines partial solutions into elegant wholes."},
            {"role": "user", "content": prompt}
        ]
        return await llm.chat(messages, use_cache=use_cache)
