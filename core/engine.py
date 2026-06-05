import time
from ..models.backends import LLMBackend
from ..config import config
from .decomposer import ProblemDecomposer
from .explorer import MultiPathExplorer
from .reasoner import DeepReasoner
from .critic import SelfCritic
from .synthesizer import Synthesizer
from .verifier import Verifier
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


class ReasoningEngine:
    def __init__(self, llm: LLMBackend = None, verbose: bool = None):
        self.llm = llm or LLMBackend()
        self.verbose = config.verbose if verbose is None else verbose
        self.display = ReasoningDisplay(verbose=self.verbose)

        self.decomposer = ProblemDecomposer(self.llm)
        self.explorer = MultiPathExplorer(self.llm)
        self.reasoner = DeepReasoner(self.llm)
        self.critic = SelfCritic(self.llm)
        self.synthesizer = Synthesizer(self.llm)
        self.verifier = Verifier(self.llm)

    def solve(self, problem: str) -> str:
        self.display.start(problem)

        orig_max_tokens = config.max_tokens
        try:
            config.max_tokens = min(orig_max_tokens, 2048)
            sub_problems = retry(lambda: self.decomposer.decompose(problem))
        finally:
            config.max_tokens = orig_max_tokens
        self.display.decomposition(sub_problems)

        all_solutions = []
        seen_topics = set()
        for i, sp in enumerate(sub_problems):
            topic_key = sp[:30].lower()
            if topic_key in seen_topics:
                continue
            seen_topics.add(topic_key)

            self.display.sub_problem_start(i + 1, sp)

            paths = retry(lambda: self.explorer.explore(sp, problem))
            self.display.paths(paths)

            best_path = paths[0] if paths else "Comprehensive analysis"
            reasoning = retry(lambda: self.reasoner.reason(sp, best_path))
            self.display.reasoning(reasoning)

            refined = retry(lambda: self.critic.critique(sp, reasoning))
            self.display.refined(refined)

            all_solutions.append(refined)

        synthesized = retry(lambda: self.synthesizer.synthesize(problem, all_solutions))
        self.display.synthesis(synthesized)

        final = retry(lambda: self.verifier.verify(problem, synthesized))
        self.display.verification(final)

        self.display.complete(final)
        return final
