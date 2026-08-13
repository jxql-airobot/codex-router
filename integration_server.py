"""Local HTTP API for TokenTracker / desktop frontends.

Uses only the Python standard library so it can run without downloading
additional dependencies.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from analytics.classification import classification_stats
from analytics.efficiency import efficiency
from analytics.heatmap import daily_activity
from analytics.statistics import breakdowns, overview
from providers.health_check import check_provider
from model_router import PROVIDER_CLASSES


ROOT = Path(__file__).resolve().parent


def _payload(data) -> bytes:
    return json.dumps(data, ensure_ascii=False).encode("utf-8")


def _routes() -> dict:
    return {
        "/api/overview": overview(),
        "/api/projects": breakdowns()["projects"],
        "/api/models": breakdowns()["models"],
        "/api/agents": breakdowns()["agents"],
        "/api/efficiency": efficiency(),
        "/api/classification": classification_stats(),
        "/api/heatmap": daily_activity(),
        "/api/health": [
            check_provider(provider_class()).to_dict()
            for provider_class in PROVIDER_CLASSES.values()
        ],
    }


class Handler(BaseHTTPRequestHandler):
    def _send(self, data: dict | list, status: int = 200) -> None:
        body = _payload(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        routes = _routes()
        if path in routes:
            self._send(routes[path])
        elif path == "/healthz":
            self._send({"ok": True})
        else:
            self._send({"error": "not found"}, status=404)

    def log_message(self, format, *args):
        return


def main(port: int = 8765) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"codex-router API: http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
