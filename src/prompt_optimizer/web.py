from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import diary
from .workflow import optimize_raw_idea

_UI_DIR = Path(__file__).resolve().parent / "ui"
_INDEX = _UI_DIR / "index.html"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7860


class OptimizerHandler(BaseHTTPRequestHandler):
    server_version = "PromptOptimizer/1.0"

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in ("/", "/index.html"):
            self._send(200, _INDEX.read_bytes(), "text/html; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/api/optimize":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
            raw_idea = str(payload.get("idea", "")).strip()
            if not raw_idea:
                self._send_json(400, {"error": "Empty idea. Give me something to work with."})
                return
            result = optimize_raw_idea(raw_idea)
            self._send_json(200, result.to_dict())
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except Exception as exc:  # pragma: no cover - defensive
            self._send_json(500, {"error": f"Optimizer failure: {exc}"})

    def _send_json(self, code: int, data: dict) -> None:
        self._send(code, json.dumps(data).encode("utf-8"), "application/json; charset=utf-8")

    def log_message(self, fmt: str, *args) -> None:  # silence default noisy logging
        pass


def create_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), OptimizerHandler)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(prog="prompt-optimizer-web", description="Terminal-style web UI for the prompt optimizer")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    print(f"prompt-optimizer running at http://{args.host}:{args.port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nshutting down")


if __name__ == "__main__":
    main()
