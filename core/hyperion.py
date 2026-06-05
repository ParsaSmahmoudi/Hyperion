"""
Next-generation Hyperion engine with:
- Async execution
- Response caching
- Multi-model routing
- Memory system
- Tool use
- Parallel sub-problem solving
"""
import asyncio
import time
import re
import os
from typing import List, Dict, Optional
from ..config import config
from ..models.router import ModelRouter
from ..models.async_backend import AsyncLLM
from ..visual.display import ReasoningDisplay
from .memory import MemoryStore
from .tools import ToolRegistry, extract_tool_calls, execute_tool_calls
from .expander import KnowledgeExpander
from .decomposer import ProblemDecomposer
from .explorer import MultiPathExplorer
from .reasoner import DeepReasoner
from .critic import SelfCritic
from .synthesizer import Synthesizer
from .verifier import Verifier
from .reflector import MetaReflector
from .searcher import DeepSearcher


class HyperionEngine:
    """The ultimate reasoning amplification engine"""

    def __init__(self, router: ModelRouter = None, memory: MemoryStore = None,
                 tools: ToolRegistry = None, verbose: bool = None,
                 use_cache: bool = True, parallel: bool = True,
                 deep_search: bool = True, use_memory: bool = True,
                 use_tools: bool = True):
        self.router = router or ModelRouter()
        self.memory = memory
        self.tools = tools if use_tools else None
        self.verbose = config.verbose if verbose is None else verbose
        self.use_cache = use_cache
        self.parallel = parallel
        self.deep_search = deep_search
        self.use_memory = use_memory
        self.display = ReasoningDisplay(verbose=self.verbose)

        self.expander = KnowledgeExpander(self.router.fast())
        self.searcher = DeepSearcher(self.router.fast())
        self.decomposer = ProblemDecomposer(self.router.fast())
        self.explorer = MultiPathExplorer(self.router.fast())
        self.reasoner = DeepReasoner(self.router.fast())
        self.critic = SelfCritic(self.router.strong())
        self.synthesizer = Synthesizer(self.router.strong())
        self.verifier = Verifier(self.router.strong())
        self.reflector = MetaReflector(self.router.strong())

        if self.memory is None and self.use_memory:
            self.memory = MemoryStore(llm=self.router.fast())

    async def _solve_sub_problem(self, sp: str, main_problem: str) -> str:
        paths_result = await self.explorer.explore(sp, main_problem, self.router.fast(), use_cache=self.use_cache)
        paths = paths_result if isinstance(paths_result, list) else [paths_result]
        best_path = paths[0] if paths else "Comprehensive analysis"
        reasoning = await self.reasoner.reason(sp, best_path, self.router.fast(), use_cache=self.use_cache)
        refined = await self.critic.critique(sp, reasoning, self.router.strong(), use_cache=self.use_cache)
        return refined

    async def solve(self, problem: str) -> str:
        self.display.start(problem)

        memory_context = ""
        if self.memory:
            try:
                memories = await self.memory.recall_smart(problem, top_k=2)
                if memories:
                    memory_context = self.memory.get_context_for(problem, top_k=2)
                    self.display._log(f"Recalled {len(memories)} relevant past solutions", "🧠")
            except Exception as e:
                self.display._log(f"Memory recall failed: {e}", "⚠️")

        context = ""
        if memory_context:
            context += memory_context + "\n\n"

        try:
            expanded = await self.expander.expand(problem, self.router.fast(), use_cache=self.use_cache)
            context += "BACKGROUND KNOWLEDGE:\n" + expanded
        except Exception as e:
            self.display._log(f"Context expansion failed: {e}", "⚠️")
        self.display._log(f"Context expanded ({len(context)} chars)", "📚")

        if self.deep_search:
            try:
                queries = await self.searcher.search(problem, self.router.fast(), use_cache=self.use_cache)
                self.display._log(f"Generated {len(queries)} knowledge queries", "🎯")
                knowledge = await self.searcher.answer_queries(queries, problem, self.router.fast(), use_cache=self.use_cache)
                knowledge_text = "\n\n".join(knowledge)
                context += f"\n\nDEEP RESEARCH:\n{knowledge_text}"
                self.display._log(f"Gathered knowledge ({len(knowledge_text)} chars)", "📖")
            except Exception as e:
                self.display._log(f"Deep search failed: {e}", "⚠️")

        enriched_problem = f"{problem}\n\nCONTEXT:\n{context}" if context else problem

        try:
            sub_problems = await self.decomposer.decompose(enriched_problem, self.router.fast(), use_cache=self.use_cache)
        except Exception as e:
            self.display._log(f"Decomposition failed: {e}", "⚠️")
            sub_problems = [problem]
        self.display.decomposition(sub_problems)

        seen = set()
        unique_subs = []
        for sp in sub_problems:
            key = sp[:30].lower()
            if key not in seen:
                seen.add(key)
                unique_subs.append(sp)

        all_solutions = []
        if self.parallel and len(unique_subs) > 1:
            self.display._log(f"Solving {len(unique_subs)} sub-problems in PARALLEL (async)", "⚡")
            tasks = [self._solve_sub_problem(sp, problem) for sp in unique_subs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for i, r in enumerate(results):
                if isinstance(r, Exception):
                    self.display._log(f"Sub-problem {i+1} failed: {r}", "❌")
                    if "API_CREDIT_LIMIT" in str(r):
                        self.display._log("API credits exhausted. Stopping early.", "⚠️")
                        break
                else:
                    all_solutions.append(r)
                    self.display.sub_problem_start(i + 1, unique_subs[i])
                    self.display._log(f"Sub-problem {i+1} complete ({len(r)} chars)", "✅")
        else:
            for i, sp in enumerate(unique_subs):
                self.display.sub_problem_start(i + 1, sp)
                result = await self._solve_sub_problem(sp, problem)
                all_solutions.append(result)

        synthesized = await self.synthesizer.synthesize(problem, all_solutions, self.router.strong(), use_cache=self.use_cache)
        self.display.synthesis(synthesized)

        verified = await self.verifier.verify(problem, synthesized, self.router.strong(), use_cache=self.use_cache)
        self.display.verification(verified)

        reflected = await self.reflector.reflect(problem, verified, all_solutions, self.router.strong(), use_cache=self.use_cache)
        self.display._log("Meta-reflection complete", "🪞")

        if self.tools:
            try:
                tool_calls = extract_tool_calls(reflected)
                if tool_calls:
                    self.display._log(f"Executing {len(tool_calls)} tool calls", "🔧")
                    tool_results = await execute_tool_calls(reflected, self.tools)
                    if tool_results:
                        reflect2 = await self.reflector.reflect(
                            problem,
                            reflected + f"\n\nTOOL RESULTS:\n{tool_results}",
                            all_solutions, self.router.strong(), use_cache=False
                        )
                        if len(reflect2) > 50:
                            reflected = reflect2
            except Exception as e:
                self.display._log(f"Tool execution failed: {e}", "⚠️")

        if self.memory:
            try:
                self.memory.store(problem, reflected, sub_problems=sub_problems)
                self.display._log("Stored in long-term memory", "💾")
            except Exception as e:
                self.display._log(f"Memory storage failed: {e}", "⚠️")

        self.display.complete(reflected)
        return reflected

    async def aclose(self):
        await self.router.aclose()


def solve_sync(problem: str, **kwargs) -> str:
    engine = HyperionEngine(**kwargs)
    try:
        return asyncio.run(engine.solve(problem))
    finally:
        asyncio.run(engine.aclose())
