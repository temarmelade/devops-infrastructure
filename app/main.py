"""Minimal HTTP service used to demonstrate the DevOps pipeline.

Endpoints:
    GET /         - service info (name, version, environment)
    GET /health   - liveness/readiness probe
    GET /metrics  - Prometheus metrics in text exposition format

Only the Python standard library is used, so the container image stays small
and there is nothing to install besides Python itself.
"""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SERVICE_NAME = "devops-app"
START_TIME = time.time()

_lock = threading.Lock()
_requests = {}


def _count(path, status):
    with _lock:
        key = (path, status)
        _requests[key] = _requests.get(key, 0) + 1


def render_metrics():
    lines = [
        "# HELP app_requests_total Total HTTP requests by path and status.",
        "# TYPE app_requests_total counter",
    ]
    with _lock:
        for (path, status), value in sorted(_requests.items()):
            lines.append(f'app_requests_total{{path="{path}",status="{status}"}} {value}')
    lines += [
        "# HELP app_uptime_seconds Seconds since the service started.",
        "# TYPE app_uptime_seconds gauge",
        f"app_uptime_seconds {time.time() - START_TIME:.3f}",
    ]
    return "\n".join(lines) + "\n"


class Handler(BaseHTTPRequestHandler):
    server_version = "devops-app"

    def _send(self, status, body, content_type="application/json"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        _count(self.path, status)

    def do_GET(self):  # noqa: N802 (name defined by BaseHTTPRequestHandler)
        if self.path == "/":
            self._send(200, json.dumps({
                "service": SERVICE_NAME,
                "version": os.getenv("APP_VERSION", "dev"),
                "environment": os.getenv("APP_ENV", "local"),
            }))
        elif self.path == "/health":
            self._send(200, json.dumps({"status": "ok"}))
        elif self.path == "/metrics":
            self._send(200, render_metrics(), "text/plain; version=0.0.4")
        else:
            self._send(404, json.dumps({"error": "not found"}))

    def log_message(self, fmt, *args):
        print(f"{self.address_string()} - {fmt % args}", flush=True)


def create_server(host="0.0.0.0", port=8080):
    return ThreadingHTTPServer((host, port), Handler)


def main():
    port = int(os.getenv("APP_PORT", "8080"))
    server = create_server(port=port)
    print(f"{SERVICE_NAME} listening on :{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
