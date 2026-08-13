"""Dashboard API data functions and optional FastAPI app."""

from __future__ import annotations

from typing import Any

from analytics.efficiency import efficiency
from analytics.heatmap import daily_activity
from analytics.statistics import breakdowns, overview, token_history
from usage.tracker import UsageTracker


def overview_data() -> dict[str, Any]:
    return overview()


def token_history_data() -> list[dict[str, Any]]:
    return token_history()


def projects_data() -> list[dict[str, Any]]:
    return breakdowns()["projects"]


def models_data() -> list[dict[str, Any]]:
    return breakdowns()["models"]


def agents_data() -> list[dict[str, Any]]:
    return breakdowns()["agents"]


def efficiency_data() -> dict[str, Any]:
    return efficiency()


def create_app():
    try:
        from fastapi import FastAPI
    except ImportError:
        return None

    app = FastAPI(title="AI开发生产力中心")

    @app.get("/api/overview")
    def _overview():
        return overview_data()

    @app.get("/api/token/history")
    def _history():
        return token_history_data()

    @app.get("/api/projects")
    def _projects():
        return projects_data()

    @app.get("/api/models")
    def _models():
        return models_data()

    @app.get("/api/agents")
    def _agents():
        return agents_data()

    @app.get("/api/efficiency")
    def _efficiency():
        return efficiency_data()

    return app
