from ..models.async_backend import AsyncLLM
from ..config import config


class DeepSearcher:
    def __init__(self, llm: AsyncLLM = None):
        self.llm = llm

    async def search(self, problem: str, llm: AsyncLLM = None, use_cache: bool = True) -> list:
        llm = llm or self.llm
        prompt = f"""I need to deeply research this problem: "{problem}"

Generate 4-6 specific KNOWLEDGE QUERIES that, if answered, would help solve this problem.
Each query should target a different aspect or dimension of the problem.
Queries should be specific, not generic.

For each query:
QUERY: [the specific knowledge query]
REASON: [why this knowledge is relevant]

Be creative and thorough. Cover different angles."""
        messages = [
            {"role": "system", "content": "You generate knowledge queries to deeply research problems."},
            {"role": "user", "content": prompt}
        ]
        result = await llm.chat(messages, use_cache=use_cache)

        queries = []
        for line in result.strip().split("\n"):
            if line.strip().upper().startswith("QUERY:"):
                q = line.strip()[6:].strip()
                if q:
                    queries.append(q)
        return queries[:5]

    async def answer_queries(self, queries: list, problem: str,
                            llm: AsyncLLM = None, use_cache: bool = True) -> list:
        llm = llm or self.llm
        answers = []
        for q in queries:
            prompt = f"""Context: I'm researching "{problem}"

Knowledge query: {q}

Provide a detailed, accurate answer based on your knowledge. Include specific facts, examples, and nuances.

ANSWER:"""
            messages = [
                {"role": "system", "content": "You have deep knowledge across all domains. Answer queries precisely and thoroughly."},
                {"role": "user", "content": prompt}
            ]
            ans = await llm.chat(messages, use_cache=use_cache)
            answers.append(f"QUERY: {q}\nANSWER: {ans}")
        return answers
