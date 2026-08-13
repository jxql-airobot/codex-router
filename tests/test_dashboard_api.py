import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import dashboard.backend.api as api


class DashboardApiTests(unittest.TestCase):
    @patch("dashboard.backend.api.overview")
    def test_overview_data(self, mock_overview):
        mock_overview.return_value = {"total_tokens": 100}
        self.assertEqual(api.overview_data()["total_tokens"], 100)

    @patch("dashboard.backend.api.token_history")
    def test_token_history_data(self, mock_history):
        mock_history.return_value = [{"date": "2026-08-13"}]
        self.assertEqual(api.token_history_data()[0]["date"], "2026-08-13")

    @patch("dashboard.backend.api.breakdowns")
    def test_projects_data(self, mock_breakdowns):
        mock_breakdowns.return_value = {"projects": [{"name": "p"}]}
        self.assertEqual(api.projects_data()[0]["name"], "p")

    @patch("dashboard.backend.api.breakdowns")
    def test_models_data(self, mock_breakdowns):
        mock_breakdowns.return_value = {"models": [{"name": "m"}]}
        self.assertEqual(api.models_data()[0]["name"], "m")

    @patch("dashboard.backend.api.breakdowns")
    def test_agents_data(self, mock_breakdowns):
        mock_breakdowns.return_value = {"agents": [{"name": "a"}]}
        self.assertEqual(api.agents_data()[0]["name"], "a")

    @patch("dashboard.backend.api.efficiency")
    def test_efficiency_data(self, mock_efficiency):
        mock_efficiency.return_value = {"commits": 3}
        self.assertEqual(api.efficiency_data()["commits"], 3)


if __name__ == "__main__":
    unittest.main()
