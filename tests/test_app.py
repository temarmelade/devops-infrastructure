import json
import threading
import unittest
import urllib.error
import urllib.request

from app.main import create_server


class AppTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server(host="127.0.0.1", port=0)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as resp:
            return resp.status, resp.read().decode()

    def test_health(self):
        status, body = self.get("/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body), {"status": "ok"})

    def test_root_returns_service_info(self):
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["service"], "devops-app")

    def test_metrics_exposes_counters(self):
        self.get("/health")
        status, body = self.get("/metrics")
        self.assertEqual(status, 200)
        self.assertIn("app_requests_total", body)
        self.assertIn("app_uptime_seconds", body)

    def test_unknown_path_returns_404(self):
        with self.assertRaises(urllib.error.HTTPError) as ctx:
            self.get("/does-not-exist")
        self.assertEqual(ctx.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
