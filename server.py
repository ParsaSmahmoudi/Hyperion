"""
Hyperion Web Server - Real-time reasoning streaming API and dashboard
Run: python -m hyperion.server
"""

import json
import os
import sys
import threading
import queue
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from .config import config
from .models.backends import LLMBackend

HOST = "127.0.0.1"
PORT = 8080

dashboard_path = os.path.join(os.path.dirname(__file__), "visual", "hyperion_dashboard.html")


class HyperionHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/dashboard":
            self._serve_dashboard()
        elif parsed.path == "/api/health":
            self._json_response({
                "status": "ok",
                "model": config.model,
                "version": "1.1.0",
                "parallel": config.parallel
            })
        else:
            self._json_response({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/hyperion":
            content_len = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_len)
            data = json.loads(body)
            question = data.get("question", "")
            streaming = data.get("stream", True)
            budget = data.get("budget", 0)

            if budget > 0:
                config.reasoning_depth = max(1, budget // 4)
                config.exploration_paths = max(1, budget // 6)

            if streaming:
                self._handle_streaming(question)
            else:
                self._handle_sync(question)
        else:
            self._json_response({"error": "not found"}, 404)

    def _serve_dashboard(self):
        try:
            with open(dashboard_path, "r", encoding="utf-8") as f:
                html = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        except FileNotFoundError:
            self._json_response({"error": "dashboard not found"}, 500)

    def _json_response(self, data: dict, status: int = 200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _setup_sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

    def _send_sse(self, data: dict):
        try:
            self.wfile.write(f"data: {json.dumps(data, ensure_ascii=False)}\n\n".encode())
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise

    def _handle_streaming(self, question: str):
        self._setup_sse()

        try:
            self._send_sse({"type": "start", "content": f"Starting Hyperion reasoning on: {question[:200]}", "model": config.model})

            if config.parallel:
                from .core.parallel_engine import ParallelReasoningEngine as Engine
            else:
                from .core.engine import ReasoningEngine as Engine

            llm = LLMBackend()
            engine = Engine(llm=llm)

            sub_problems = engine.decomposer.decompose(question)
            self._send_sse({
                "type": "decompose",
                "content": f"Decomposed into {len(sub_problems)} sub-problems:\n\n" + "\n".join(f"**SP{i+1}:** {s}" for i, s in enumerate(sub_problems)),
                "subProblems": len(sub_problems),
                "list": sub_problems
            })

            seen = set()
            unique_subs = []
            for sp in sub_problems:
                key = sp[:30].lower()
                if key not in seen:
                    seen.add(key)
                    unique_subs.append(sp)

            all_solutions = []

            if config.parallel and len(unique_subs) > 1:
                self._send_sse({"type": "info", "content": f"Solving {len(unique_subs)} sub-problems in PARALLEL"})

                results = {}
                threads = []
                lock = threading.Lock()

                def solve_worker(sp_idx, sp_text):
                    try:
                        paths = engine.explorer.explore(sp_text, question)
                        self._send_sse({
                            "type": "explore",
                            "subProblem": sp_idx + 1,
                            "content": f"**SP{sp_idx+1}:** Explored {len(paths)} approaches:\n\n" + "\n".join(f"• {p[:100]}..." for p in paths),
                            "paths": len(paths)
                        })

                        best = paths[0] if paths else "Analysis"
                        reasoning = engine.reasoner.reason(sp_text, best)
                        self._send_sse({
                            "type": "reason",
                            "subProblem": sp_idx + 1,
                            "content": f"**SP{sp_idx+1}:** Deep reasoning complete ({len(reasoning)} chars)\n\n{reasoning[:300]}..."
                        })

                        refined = engine.critic.critique(sp_text, reasoning)
                        self._send_sse({
                            "type": "critic",
                            "subProblem": sp_idx + 1,
                            "content": f"**SP{sp_idx+1}:** Critique & refinement complete ({len(refined)} chars)\n\n{refined[:300]}..."
                        })

                        with lock:
                            results[sp_idx] = refined
                    except Exception as e:
                        with lock:
                            results[sp_idx] = f"Error: {e}"

                for i, sp in enumerate(unique_subs):
                    t = threading.Thread(target=solve_worker, args=(i, sp))
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join()

                for i in range(len(unique_subs)):
                    if i in results:
                        all_solutions.append(results[i])
            else:
                for i, sp in enumerate(unique_subs):
                    self._send_sse({"type": "progress", "subProblem": i + 1, "total": len(unique_subs)})

                    paths = engine.explorer.explore(sp, question)
                    self._send_sse({
                        "type": "explore",
                        "subProblem": i + 1,
                        "content": f"**SP{i+1}:** Explored {len(paths)} approaches:\n\n" + "\n".join(f"• {p[:100]}..." for p in paths),
                        "paths": len(paths)
                    })

                    best = paths[0] if paths else "Analysis"
                    reasoning = engine.reasoner.reason(sp, best)
                    self._send_sse({
                        "type": "reason",
                        "subProblem": i + 1,
                        "content": f"**SP{i+1}:** Deep reasoning complete ({len(reasoning)} chars)\n\n{reasoning[:300]}..."
                    })

                    refined = engine.critic.critique(sp, reasoning)
                    self._send_sse({
                        "type": "critic",
                        "subProblem": i + 1,
                        "content": f"**SP{i+1}:** Critique done ({len(refined)} chars)\n\n{refined[:300]}..."
                    })

                    all_solutions.append(refined)

            self._send_sse({"type": "synthesize", "content": f"Synthesizing {len(all_solutions)} solutions into final answer..."})

            synthesized = engine.synthesizer.synthesize(question, all_solutions)
            self._send_sse({
                "type": "synthesis",
                "content": f"Synthesis complete ({len(synthesized)} chars)\n\n{synthesized[:500]}...",
                "chars": len(synthesized)
            })

            verified = engine.verifier.verify(question, synthesized)
            self._send_sse({
                "type": "verify",
                "content": f"Verification complete\n\n{verified[:400]}..."
            })

            reflected = engine.reflector.reflect(question, verified, all_solutions)
            self._send_sse({
                "type": "reflect",
                "content": f"Meta-reflection complete\n\n{reflected[:400]}..."
            })

            self._send_sse({
                "type": "complete",
                "content": reflected,
                "tokens": sum(len(s) // 4 for s in all_solutions)
            })

        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            try:
                self._send_sse({"type": "error", "content": f"Error: {str(e)}"})
            except:
                pass

    def _handle_sync(self, question: str):
        if not question:
            self._json_response({"error": "no question provided"}, 400)
            return

        try:
            if config.parallel:
                from .core.parallel_engine import ParallelReasoningEngine as Engine
            else:
                from .core.engine import ReasoningEngine as Engine

            llm = LLMBackend()
            engine = Engine(llm=llm)
            answer = engine.solve(question)

            self._json_response({
                "answer": answer,
                "model": config.model
            })
        except Exception as e:
            self._json_response({"error": str(e)}, 500)

    def log_message(self, format, *args):
        pass


def run_server(host: str = HOST, port: int = PORT):
    server = HTTPServer((host, port), HyperionHandler)
    print(f"\n{'='*50}")
    print(f"  HYPERION REASONING ENGINE v1.1")
    print(f"{'='*50}")
    print(f"  Dashboard: http://{host}:{port}/dashboard")
    print(f"  API:       http://{host}:{port}/api/hyperion")
    print(f"  Health:    http://{host}:{port}/api/health")
    print(f"  Model:     {config.model}")
    print(f"  Parallel:  {config.parallel}")
    print(f"  Depth:     {config.reasoning_depth}")
    print(f"  Paths:     {config.exploration_paths}")
    print(f"{'='*50}")
    print(f"  Press Ctrl+C to stop")
    print(f"{'='*50}\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
