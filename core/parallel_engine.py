import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from ..models.backends import LLMBackend
from ..config import config
from .decomposer import ProblemDecomposer
from .explorer import MultiPathExplorer
from .reasoner import DeepReasoner
from .critic import SelfCritic
from .synthesizer import Synthesizer
from .verifier import Verifier
from .expander import KnowledgeExpander
from .reflector import MetaReflector
from .searcher import DeepSearcher
from ..visual.display import ReasoningDisplay


def retry(func, max_retries=2, delay=2):
    for attempt in range(max_retries + 1):
        try:
            return func()
        except Exception as e:
            if attempt < max_retries:
                time.sleep(delay * (attempt + 1))
                continue
            raise


class ParallelReasoningEngine:
    def __init__(self, llm: LLMBackend = None, verbose: bool = None, parallel: bool = True):
        self.llm = llm or LLMBackend()
        self.parallel = parallel and config.exploration_paths > 1
        self.verbose = config.verbose if verbose is None else verbose
        self.display = ReasoningDisplay(verbose=self.verbose)

        self.searcher = DeepSearcher(self.llm)
        self.expander = KnowledgeExpander(self.llm)
        self.decomposer = ProblemDecomposer(self.llm)
        self.explorer = MultiPathExplorer(self.llm)
        self.reasoner = DeepReasoner(self.llm)
        self.critic = SelfCritic(self.llm)
        self.synthesizer = Synthesizer(self.llm)
        self.verifier = Verifier(self.llm)
        self.reflector = MetaReflector(self.llm)

    def _solve_sub_problem(self, sp: str, main_problem: str) -> str:
        paths = retry(lambda: self.explorer.explore(sp, main_problem))
        best_path = paths[0] if paths else "Comprehensive analysis"
        reasoning = retry(lambda: self.reasoner.reason(sp, best_path))
        refined = retry(lambda: self.critic.critique(sp, reasoning))
        return refined

    def solve(self, problem: str, deep_search: bool = True) -> str:
        self.display.start(problem)

        orig_t = config.max_tokens
        try:
            config.max_tokens = min(orig_t, 2048)
            context = retry(lambda: self.expander.expand(problem))
        finally:
            config.max_tokens = orig_t
        self.display._log(f"Context expanded ({len(context)} chars)", "📚")

        if deep_search:
            try:
                config.max_tokens = min(orig_t, 2048)
                queries = retry(lambda: self.searcher.search(problem))
                self.display._log(f"Generated {len(queries)} knowledge queries", "🎯")

                config.max_tokens = min(orig_t, 1536)
                knowledge = retry(lambda: self.searcher.answer_queries(queries, problem))
                knowledge_text = "\n\n".join(knowledge)
                self.display._log(f"Gathered knowledge ({len(knowledge_text)} chars)", "📚")
                context = context + "\n\n" + knowledge_text
            finally:
                config.max_tokens = orig_t

        enriched_problem = f"{problem}\n\nCONTEXT:\n{context}"

        orig_t2 = config.max_tokens
        try:
            config.max_tokens = min(orig_t2, 2048)
            sub_problems = retry(lambda: self.decomposer.decompose(enriched_problem))
        finally:
            config.max_tokens = orig_t2
        self.display.decomposition(sub_problems)

        seen = set()
        unique_subs = []
        for sp in sub_problems:
            key = sp[:30].lower()
            if key not in seen:
                seen.add(key)
                unique_subs.append(sp)

        all_solutions = []
        credits_ok = True
        if self.parallel and len(unique_subs) > 1 and credits_ok:
            self.display._log(f"Solving {len(unique_subs)} sub-problems in PARALLEL", "⚡")
            with ThreadPoolExecutor(max_workers=min(len(unique_subs), 3)) as executor:
                fut_map = {executor.submit(self._solve_sub_problem, sp, problem): sp for sp in unique_subs}
                for future in as_completed(fut_map):
                    sp = fut_map[future]
                    try:
                        result = future.result()
                        all_solutions.append(result)
                        idx = unique_subs.index(sp) + 1
                        self.display.sub_problem_start(idx, sp)
                        self.display._log(f"Sub-problem {idx} complete ({len(result)} chars)", "✅")
                    except Exception as e:
                        if "API_CREDIT_LIMIT" in str(e):
                            credits_ok = False
                            self.display._log("API credits exhausted. Completing with available results.", "⚠️")
                        else:
                            self.display._log(f"Sub-problem failed: {e}", "❌")
        elif credits_ok:
            for i, sp in enumerate(unique_subs):
                self.display.sub_problem_start(i + 1, sp)
                result = self._solve_sub_problem(sp, problem)
                all_solutions.append(result)

        synthesized = retry(lambda: self.synthesizer.synthesize(problem, all_solutions))
        self.display.synthesis(synthesized)

        verified = retry(lambda: self.verifier.verify(problem, synthesized))
        self.display.verification(verified)

        reflected = retry(lambda: self.reflector.reflect(problem, verified, all_solutions))
        self.display._log("Meta-reflection complete", "🪞")

        self.display.complete(reflected)
        return reflected
