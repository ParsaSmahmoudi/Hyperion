import sys
from datetime import datetime
from ..config import config


class ReasoningDisplay:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.start_time = None
        self.steps = []

    def _log(self, msg: str, emoji: str = ""):
        if self.verbose:
            ts = datetime.now().strftime("%H:%M:%S")
            print(f"{emoji} [{ts}] {msg}", file=sys.stderr)
            sys.stderr.flush()

    def _separator(self, char: str = "=", n: int = 60):
        if self.verbose:
            print(char * n, file=sys.stderr)

    def start(self, problem: str):
        self.start_time = datetime.now()
        self._separator("=")
        self._log(f"HYPERION REASONING ENGINE v1.0", "🧠")
        self._separator("=")
        self._log(f"Problem: {problem[:100]}{'...' if len(problem) > 100 else ''}", "📋")
        self._log(f"Model: {config.model}", "⚙️")
        self._log(f"Depth: {config.reasoning_depth} | Paths: {config.exploration_paths} | Critic rounds: {config.critic_rounds}")
        self._separator("-")

    def decomposition(self, sub_problems: list):
        self._log(f"Decomposed into {len(sub_problems)} sub-problems", "🔍")
        for i, sp in enumerate(sub_problems, 1):
            preview = sp[:80].replace("\n", " ")
            self._log(f"  [{i}] {preview}...")

    def sub_problem_start(self, idx: int, sub_problem: str):
        self._separator("─")
        self._log(f"Sub-problem {idx}: {sub_problem[:80]}...", "🎯")

    def paths(self, paths: list):
        self._log(f"Explored {len(paths)} reasoning paths", "🛤️")
        for i, p in enumerate(paths, 1):
            preview = p[:60].replace("\n", " ")
            self._log(f"  Path {i}: {preview}...")

    def reasoning(self, reasoning: str):
        self._log(f"Deep reasoning complete ({len(reasoning)} chars)", "💭")

    def refined(self, refined: str):
        self._log(f"Self-critique complete ({len(refined)} chars)", "🔧")

    def synthesis(self, synthesized: str):
        self._log(f"Synthesis complete ({len(synthesized)} chars)", "🔄")

    def verification(self, final: str):
        self._log(f"Verification complete", "✅")

    def complete(self, answer: str):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        self._separator("=")
        self._log(f"HYPERION COMPLETE in {elapsed:.1f}s", "🏆")
        self._log(f"Final answer: {len(answer)} chars", "📝")
        self._separator("=")
