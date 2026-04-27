"""Tests for active domain routers."""
import os


def test_endpoints_py_deleted():
    """endpoints.py must not exist after the router split."""
    endpoints_path = os.path.join(
        os.path.dirname(__file__), "..", "app", "api", "endpoints.py"
    )
    assert not os.path.exists(os.path.abspath(endpoints_path)), (
        "backend/app/api/endpoints.py still exists — router split not complete"
    )


def test_all_routes_registered():
    """
    Active domain router modules must exist and expose a `router` attribute after the split.
    main.py must import from domain routers, not endpoints.py.
    """
    expected_routers = ["stocks", "macro", "intelligence", "admin", "portfolio_v2"]
    for module_name in expected_routers:
        try:
            import importlib
            mod = importlib.import_module(f"app.api.{module_name}")
            assert hasattr(mod, "router"), (
                f"app.api.{module_name} has no `router` attribute"
            )
        except ImportError as e:
            pytest.fail(f"Could not import app.api.{module_name}: {e}")
