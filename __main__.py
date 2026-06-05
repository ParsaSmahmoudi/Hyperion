"""
HYPERION - Advanced Reasoning Amplification Engine

Usage:
    python -m hyperion "Your complex question"
    python -m hyperion --interactive
    python -m hyperion --server
"""
import os
import sys
import asyncio
import argparse

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.markdown import Markdown

from .config import config
from .core.hyperion import HyperionEngine, solve_sync
from .models.router import ModelRouter

console = Console()


def print_banner():
    banner = """
    ╔══════════════════════════════════════════════════════╗
    ║                                                      ║
    ║    ██╗  ██╗██╗   ██╗██████╗ ███████╗██████╗           ║
    ║    ██║  ██║╚██╗ ██╔╝██╔══██╗██╔════╝██╔══██╗          ║
    ║    ███████║ ╚████╔╝ ██████╔╝█████╗  ██████╔╝          ║
    ║    ██╔══██║  ╚██╔╝  ██╔═══╝ ██╔══╝  ██╔══██╗          ║
    ║    ██║  ██║   ██║   ██║     ███████╗██║  ██║          ║
    ║    ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝          ║
    ║                                                      ║
    ║       Reasoning Amplification Engine v2.0            ║
    ╚══════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold cyan")
    console.print(f"  Model: [green]{config.model}[/green] | Backend: [yellow]{config.backend}[/yellow]")
    console.print(f"  Depth: [green]{config.reasoning_depth}[/green] | Paths: [green]{config.exploration_paths}[/green] | Parallel: [green]{config.parallel}[/green]")
    console.print()


def parse_args():
    parser = argparse.ArgumentParser(
        description="HYPERION - Amplify any LLM's reasoning power exponentially",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m hyperion "What is consciousness?"
  python -m hyperion --depth 3 --paths 3 "Solve complex problem"
  python -m hyperion --interactive
  python -m hyperion --server
        """
    )
    parser.add_argument("question", nargs="*", help="The question/problem to reason about")
    parser.add_argument("--model", "-m", help=f"LLM model (default: {config.model})")
    parser.add_argument("--fast-model", help="Fast model for exploration (uses auto-detect if not set)")
    parser.add_argument("--strong-model", help="Strong model for synthesis (uses auto-detect if not set)")
    parser.add_argument("--backend", "-b", default=config.backend, choices=["openai", "openrouter", "ollama"])
    parser.add_argument("--api-key", "-k", help="API key")
    parser.add_argument("--base-url", "-u", help="API base URL")
    parser.add_argument("--depth", "-d", type=int, default=config.reasoning_depth)
    parser.add_argument("--paths", "-p", type=int, default=config.exploration_paths)
    parser.add_argument("--budget", type=int, default=0, help="Thinking budget (higher=more thorough)")
    parser.add_argument("--no-cache", action="store_true", help="Disable response caching")
    parser.add_argument("--no-parallel", action="store_true", help="Disable parallel sub-problem solving")
    parser.add_argument("--no-memory", action="store_true", help="Disable long-term memory")
    parser.add_argument("--no-tools", action="store_true", help="Disable tool use")
    parser.add_argument("--no-deep-search", action="store_true", help="Disable deep knowledge search")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive CLI")
    parser.add_argument("--server", "-s", action="store_true", help="Start web server")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode")
    return parser.parse_args()


async def interactive_mode(args):
    from .core.hyperion import HyperionEngine
    from .core.memory import MemoryStore
    from .core.tools import ToolRegistry

    print_banner()
    console.print("[bold green]HYPERION INTERACTIVE MODE[/bold green]")
    console.print("Commands: [cyan]exit[/cyan], [cyan]/config[/cyan], [cyan]/tools[/cyan], [cyan]/memory-clear[/cyan]\n")

    router = ModelRouter(
        backend=config.backend,
        api_key=config.api_key,
        base_url=config.base_url,
        fast_model=args.fast_model,
        strong_model=args.strong_model
    )
    memory = MemoryStore(llm=router.fast())
    tools = ToolRegistry()
    engine = HyperionEngine(
        router=router, memory=memory, tools=tools,
        use_cache=not args.no_cache,
        parallel=not args.no_parallel,
        use_memory=not args.no_memory,
        use_tools=not args.no_tools,
        deep_search=not args.no_deep_search,
        verbose=False
    )

    while True:
        try:
            question = console.input("[bold green]🧠 > [/bold green]").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            break
        if question.lower() == "/config":
            console.print(f"  Model:    {config.model}")
            console.print(f"  Fast:     {router.fast_model}")
            console.print(f"  Strong:   {router.strong_model}")
            console.print(f"  Depth:    {config.reasoning_depth}")
            console.print(f"  Paths:    {config.exploration_paths}")
            console.print(f"  Parallel: {not args.no_parallel}")
            console.print(f"  Memory:   {not args.no_memory}")
            console.print(f"  Tools:    {not args.no_tools}")
            continue
        if question.lower() == "/tools":
            console.print(tools.describe())
            continue
        if question.lower() == "/memory-clear":
            memory.clear()
            console.print("  Memory cleared.")
            continue
        if question.lower() == "/help":
            console.print("  Commands: [cyan]exit[/cyan], [cyan]/config[/cyan], [cyan]/tools[/cyan], [cyan]/memory-clear[/cyan]")
            continue

        console.print()
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=30),
                TimeElapsedColumn(),
                transient=True
            ) as progress:
                task = progress.add_task("[cyan]Hyperion thinking...", total=100)
                # We can't easily stream the engine's progress, so just show a spinner
                answer = await engine.solve(question)
                progress.update(task, completed=100)
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")
            continue

        console.print(Panel(Markdown(answer), title="[bold green]✓ FINAL ANSWER[/bold green]", border_style="green"))
        console.print()

    await engine.aclose()


async def solve_async(question, args) -> str:
    from .core.hyperion import HyperionEngine
    from .core.memory import MemoryStore
    from .core.tools import ToolRegistry

    router = ModelRouter(
        backend=config.backend,
        api_key=config.api_key,
        base_url=config.base_url,
        fast_model=args.fast_model,
        strong_model=args.strong_model
    )
    memory = MemoryStore(llm=router.fast()) if not args.no_memory else None
    tools = ToolRegistry() if not args.no_tools else None
    engine = HyperionEngine(
        router=router, memory=memory, tools=tools,
        use_cache=not args.no_cache,
        parallel=not args.no_parallel,
        use_memory=not args.no_memory,
        use_tools=not args.no_tools,
        deep_search=not args.no_deep_search,
        verbose=not args.quiet
    )

    try:
        answer = await engine.solve(question)
        return answer
    finally:
        await engine.aclose()


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
    if args.budget > 0:
        config.reasoning_depth = max(1, args.budget // 4)
        config.exploration_paths = max(1, args.budget // 6)
        config.critic_rounds = max(1, args.budget // 8)
    if args.quiet:
        config.verbose = False

    if args.server:
        from .server import run_server
        run_server()
        return

    if args.interactive:
        asyncio.run(interactive_mode(args))
        return

    question = " ".join(args.question) if args.question else ""
    if not question:
        question = console.input("[bold]Enter your question:[/bold] ").strip()
    if not question:
        console.print("[red]No question provided. Use --help for usage.[/red]")
        sys.exit(1)

    if not args.quiet:
        print_banner()

    answer = asyncio.run(solve_async(question, args))
    if not args.quiet:
        console.print(Panel(Markdown(answer), title="[bold green]✓ FINAL ANSWER[/bold green]", border_style="green"))
    else:
        print(answer)


if __name__ == "__main__":
    main()
