"""
Long-term memory system for Hyperion.
Stores previous reasoning sessions, retrieves relevant ones for new queries.
"""
import os
import json
import time
import hashlib
from typing import List, Dict, Optional
from pathlib import Path
from ..models.async_backend import AsyncLLM, get_cache


class MemoryStore:
    """Persistent memory across conversations"""

    def __init__(self, memory_dir: str = None, llm: AsyncLLM = None):
        self.memory_dir = Path(memory_dir or os.path.expanduser("~/.hyperion_memory"))
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.memory_dir / "index.json"
        self.llm = llm

    def _load_index(self) -> List[Dict]:
        if self.index_path.exists():
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return []

    def _save_index(self, index: List[Dict]):
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)

    def _key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]

    def store(self, problem: str, solution: str, sub_problems: List[str] = None,
              tags: List[str] = None) -> str:
        key = self._key(problem + str(time.time()))
        record = {
            "id": key,
            "timestamp": time.time(),
            "problem": problem,
            "solution": solution,
            "sub_problems": sub_problems or [],
            "tags": tags or [],
            "summary": problem[:200]
        }

        path = self.memory_dir / f"{key}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)

        index = self._load_index()
        index.append({"id": key, "timestamp": record["timestamp"],
                      "summary": record["summary"], "tags": record["tags"]})
        self._save_index(index)
        return key

    def recall(self, problem: str, top_k: int = 3) -> List[Dict]:
        """Find relevant past sessions using simple keyword matching"""
        index = self._load_index()
        if not index:
            return []

        problem_words = set(problem.lower().split())
        scored = []
        for entry in index:
            entry_words = set(entry.get("summary", "").lower().split())
            entry_words.update(" ".join(entry.get("tags", [])).lower().split())
            if not entry_words:
                continue
            overlap = len(problem_words & entry_words)
            if overlap > 0:
                scored.append((overlap, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, entry in scored[:top_k]:
            path = self.memory_dir / f"{entry['id']}.json"
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    results.append(json.load(f))
        return results

    async def recall_smart(self, problem: str, top_k: int = 3) -> List[Dict]:
        """Use LLM to assess relevance of past memories"""
        candidates = self.recall(problem, top_k=top_k * 3)
        if not candidates or not self.llm:
            return candidates[:top_k]

        prompt = f"""Given the NEW PROBLEM: "{problem}"

Past solutions (numbered):
"""
        for i, c in enumerate(candidates):
            prompt += f"{i+1}. {c.get('summary', '')}\n"

        prompt += "\nWhich past solutions (by number) are RELEVANT to the new problem? Return comma-separated numbers, or 'none' if none are relevant."

        messages = [
            {"role": "system", "content": "You judge relevance between problems."},
            {"role": "user", "content": prompt}
        ]
        try:
            response = await self.llm.chat(messages)
            import re
            numbers = re.findall(r'\d+', response)
            indices = [int(n) - 1 for n in numbers if 0 < int(n) <= len(candidates)]
            return [candidates[i] for i in indices if 0 <= i < len(candidates)][:top_k]
        except Exception:
            return candidates[:top_k]

    def get_context_for(self, problem: str, top_k: int = 2) -> str:
        memories = self.recall(problem, top_k)
        if not memories:
            return ""
        ctx = "PREVIOUS RELEVANT SOLUTIONS:\n\n"
        for i, m in enumerate(memories, 1):
            ctx += f"--- Memory {i} (Q: {m['summary'][:80]}...) ---\n{m['solution'][:500]}\n\n"
        return ctx

    def clear(self):
        for f in self.memory_dir.glob("*.json"):
            f.unlink()
