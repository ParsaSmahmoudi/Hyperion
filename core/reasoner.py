import os
from ..models.async_backend import AsyncLLM
from ..config import config


class DeepReasoner:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def reason(self, sub_problem: str, approach: str,
                     llm: AsyncLLM = None, use_cache: bool = True) -> str:
        llm = llm or self.llm
        max_depth = config.reasoning_depth
        full_reasoning = []

        for depth in range(1, max_depth + 1):
            depth_instructions = {
                1: "surface-level analysis and first principles",
                2: "deeper implications, hidden assumptions, and connections",
                3: "novel insights, edge cases, and interdisciplinary perspectives",
                4: "meta-reasoning - analyze the reasoning process itself",
                5: "synthesis - combine all depths into a unified understanding"
            }
            di = depth_instructions.get(depth, f"deep analysis at level {depth}")

            prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "reason.txt")
            with open(prompt_path, "r", encoding="utf-8") as f:
                template = f.read()
            prompt = template.replace("{sub_problem}", sub_problem)\
                           .replace("{approach}", approach)\
                           .replace("{depth_level}", str(depth))\
                           .replace("{max_depth}", str(max_depth))\
                           .replace("{depth_instruction}", di)
            context = "\n\n".join(full_reasoning[-3:]) if full_reasoning else "No prior reasoning yet."

            messages = [
                {"role": "system", "content": "You are an extremely thorough reasoning engine. You leave no stone unturned."},
                {"role": "user", "content": prompt + f"\n\nPRIOR REASONING:\n{context}"}
            ]
            result = await llm.chat(messages, use_cache=use_cache)
            full_reasoning.append(result)

        return "\n\n=== DEEPER REASONING ===\n\n".join(full_reasoning)
