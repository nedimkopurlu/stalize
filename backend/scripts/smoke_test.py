"""Production smoke test for core Stalize surfaces.

Runs read-only checks against the local backend and frontend.
Fails fast when one of the critical decision surfaces is broken.
"""

from __future__ import annotations

import json
import sys
from typing import Any

import requests


BACKEND = "http://localhost:8000"
FRONTEND = "http://localhost:3000"


def _get_json(url: str) -> Any:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


def _get_status(url: str) -> int:
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.status_code


def main() -> int:
    checks = {
        "frontend_home": _get_status(f"{FRONTEND}/"),
        "frontend_model_portfolio": _get_status(f"{FRONTEND}/model-portfolio"),
        "health": _get_json(f"{BACKEND}/api/health"),
        "dashboard": _get_json(f"{BACKEND}/api/dashboard"),
        "intelligence": _get_json(f"{BACKEND}/api/intelligence/overview?limit=8"),
        "score_breakdown": _get_json(f"{BACKEND}/api/stocks/THYAO/score-breakdown"),
        "model_portfolio": _get_json(f"{BACKEND}/api/model-portfolio/current"),
        "model_portfolio_history": _get_json(f"{BACKEND}/api/model-portfolio/history?limit=4"),
        "source_catalog": _get_json(f"{BACKEND}/api/sources/catalog"),
        "source_health_history": _get_json(f"{BACKEND}/api/sources/health/history?limit=5"),
    }

    health = checks["health"]
    if health.get("status") not in {"ok", "healthy", "degraded"}:
        raise RuntimeError(f"Unexpected health state: {health.get('status')}")

    score_breakdown = checks["score_breakdown"]["breakdown"]
    if len(score_breakdown.get("components", [])) < 3:
        raise RuntimeError("Contextual score breakdown is incomplete")

    if "horizon_summary" not in checks["intelligence"]:
        raise RuntimeError("Intelligence overview missing horizon summary")

    source_summary = checks["source_catalog"].get("summary") or {}
    if source_summary.get("total", 0) <= 0:
        raise RuntimeError("Source catalog is empty")

    if "weeks" not in checks["model_portfolio_history"]:
        raise RuntimeError("Model portfolio history payload is invalid")

    print(json.dumps(checks, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise
