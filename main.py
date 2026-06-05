"""
HYPERION - Advanced Reasoning Amplification Engine

Usage:
    python -m hyperion.main "Your complex question here"
    python -m hyperion.main --interactive
    python -m hyperion.server
    python -m hyperion.main --model openai/gpt-4o --depth 3 --paths 3 "Your question"
"""

import sys
import os
import argparse
from .config import config
from .models.backends import LLMBackend


def parse_args():
    parser = argparse.ArgumentParser(
        description="HYPERION - Amplify any LLM's reasoning power exponentially",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hyperion.main "What is consciousness?"
  python -m hyperion.main --depth 3 --paths 3 "Solve complex problem"
  python -m hyperion.main --api-key sk-xxx --backend openai "Your question"
  python -m hyperion.main --interactive
  python -m hyperion.server          # Web dashboard
        """
    )
    parser.add_argument("question", nargs="*", help="The question/problem to reason about")
    parser.add_argument("--model", "-m", help=f"LLM model (default: {config.model})")
    parser.add_argument("--backend", "-b", default=config.backend,
                        choices=["openai", "openrouter", "ollama"],
                        help=f"LLM backend (default: {config.backend})")
    parser.add_argument("--api-key", "-k", help="API key for the LLM backend")
    parser.add_argument("--base-url", "-u", help="Base URL for the API")
    parser.add_argument("--depth", "-d", type=int, default=config.reasoning_depth,
                        help=f"Reasoning depth (default: {config.reasoning_depth})")
    parser.add_argument("--paths", "-p", type=int, default=config.exploration_paths,
                        help=f"Exploration paths per sub-problem (default: {config.exploration_paths})")
    parser.add_argument("--budget", type=int, default=0,
                        help="Thinking budget (0=auto, higher=more thorough)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress verbose output")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive CLI mode")
    parser.add_argument("--sequential", action="store_true", help="Disable parallel solving")
    return parser.parse_args()


def interactive_mode(engine_class, llm):
    engine = engine_class(llm=llm)
    print(f"\n{'='*50}")
    print(f"  HYPERION INTERACTIVE REASONING")
    print(f"{'='*50}")
    print(f"  Model: {config.model}")
    print(f"  Depth: {config.reasoning_depth} | Paths: {config.exploration_paths}")
    print(f"  Type 'exit' to stop, '/config' for settings")
    print(f"{'='*50}\n")

    while True:
        try:
            question = input("🧠 > ").strip()
            if not question:
                continue
            if question.lower() in ("exit", "quit"):
                break
            if question.lower() == "/config":
                print(f"  Model: {config.model}")
                print(f"  Backend: {config.backend}")
                print(f"  Depth: {config.reasoning_depth}")
                print(f"  Paths: {config.exploration_paths}")
                print(f"  Parallel: {config.parallel}")
                continue
            if question.lower() == "/help":
                print("  Commands: exit, quit, /config, /help")
                continue

            print()
            answer = engine.solve(question)
            print(f"\n{'='*50}")
            print("  FINAL ANSWER:")
            print(f"{'='*50}")
            print(answer)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def main():
    args = parse_args()

    if args.model:
        config.model = args.model
    if args.backend:
        config.backend = args.backend
    if args.api_key:
        config.api_key = args.api_key
    if args.base_url:
        config.base_url = args.base_url
    if args.depth:
        config.reasoning_depth = args.depth
    if args.paths:
        config.exploration_paths = args.paths
    if args.sequential:
        config.parallel = False
    if args.quiet:
        config.verbose = False

    if args.budget > 0:
        config.reasoning_depth = max(1, args.budget // 4)
        config.exploration_paths = max(1, args.budget // 6)
        config.critic_rounds = max(1, args.budget // 8)

    llm = LLMBackend(
        backend=config.backend,
        api_key=config.api_key,
        model=config.model
    )

    if config.parallel:
        from .core.parallel_engine import ParallelReasoningEngine as Engine
    else:
        from .core.engine import ReasoningEngine as Engine

    if args.interactive:
        interactive_mode(Engine, llm)
        return

    question = " ".join(args.question) if args.question else ""
    if not question:
        question = input("Enter your question: ").strip()
    if not question:
        print("No question provided. Use --help for usage info.")
        sys.exit(1)

    engine = Engine(llm=llm, verbose=config.verbose)
    answer = engine.solve(question)
    print(f"\n{'='*50}")
    print("  FINAL ANSWER:")
    print(f"{'='*50}")
    print(answer)


if __name__ == "__main__":
    main()
