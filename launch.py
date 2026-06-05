"""
Hyperion Launcher - Start the reasoning engine in different modes

Usage:
    python launch.py            # Interactive CLI mode
    python launch.py --web      # Web dashboard mode
    python launch.py --question "your question"  # Direct question mode
"""

import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="HYPERION Reasoning Engine Launcher")
    parser.add_argument("--web", "-w", action="store_true", help="Start web dashboard")
    parser.add_argument("--question", "-q", nargs="+", help="Question to answer")
    parser.add_argument("--model", "-m", help="LLM model")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive CLI mode")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Web server port")

    args = parser.parse_args()

    if args.model:
        from .config import config
        config.model = args.model

    if args.web:
        from .server import run_server
        run_server(port=args.port)
        return

    if args.question:
        question = " ".join(args.question)
        from .main import main as cli_main
        sys.argv = ["hyperion"] + args.question
        cli_main()
        return

    from .main import interactive_mode
    from .models.backends import LLMBackend
    from .core.engine import ReasoningEngine

    llm = LLMBackend()
    engine = ReasoningEngine(llm=llm)
    interactive_mode(engine)


if __name__ == "__main__":
    main()
