import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from integration_server import _routes


class IntegrationServerTests(unittest.TestCase):
    def test_routes_include_core_endpoints(self):
        routes = _routes()
        for key in (
            "/api/overview",
            "/api/projects",
            "/api/models",
            "/api/agents",
            "/api/efficiency",
            "/api/classification",
            "/api/heatmap",
            "/api/health",
        ):
            self.assertIn(key, routes)

    def test_overview_has_tokens(self):
        self.assertIn("total_tokens", _routes()["/api/overview"])

    def test_health_is_list(self):
        self.assertIsInstance(_routes()["/api/health"], list)


if __name__ == "__main__":
    unittest.main()
