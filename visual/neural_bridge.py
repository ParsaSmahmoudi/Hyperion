"""
Bridge between Hyperion reasoning engine and LARP neural visualization system.
Sends real-time reasoning signals to the visual network.
"""

import json
import socket
import threading
import time
from ..config import config


class NeuralBridge:
    """Sends reasoning signals to LARP visualization nodes"""

    def __init__(self, enabled: bool = True, target_port: int = 3003):
        self.enabled = enabled and config.verbose
        self.target_port = target_port
        self.sock = None
        self._connect()

    def _connect(self):
        if not self.enabled:
            return
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(2)
            self.sock.connect(("127.0.0.1", self.target_port))
        except (socket.timeout, ConnectionRefusedError, OSError):
            self.sock = None
            if self.enabled:
                pass

    def send_signal(self, signal_type: str, data: dict = None):
        if not self.sock:
            return
        try:
            packet = json.dumps({
                "type": signal_type,
                "from": "HYPERION",
                "to": "CORE",
                "payload": data or {},
                "timestamp": time.time()
            })
            self.sock.sendall((packet + "\n").encode())
        except (BrokenPipeError, OSError):
            self.sock = None

    def emit_reasoning_start(self, sub_problem_idx: int):
        self.send_signal("reasoning_start", {"sub_problem": sub_problem_idx})

    def emit_thought(self, thought: str, intensity: float = 0.5):
        self.send_signal("thought", {"content": thought[:50], "intensity": intensity})

    def emit_critique(self, flaws: int):
        self.send_signal("critique", {"flaws_found": flaws})

    def emit_synthesis(self, num_sources: int):
        self.send_signal("synthesis", {"sources": num_sources})

    def emit_complete(self):
        self.send_signal("complete", {})

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None
