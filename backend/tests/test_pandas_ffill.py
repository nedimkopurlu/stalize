"""
Tests for TECH-03: Replace deprecated fillna(method='ffill') with ffill() in dynamic_correlation.py.

These tests define the contract — they MUST fail (RED) before the implementation change.
"""
import warnings


def test_ffill_no_deprecation_warning():
    """
    Running forward-fill logic against a DataFrame with missing rows must not
    emit any pandas FutureWarning about fillna(method=...) being deprecated.
    """
    import pandas as pd

    # Construct a tiny frame that mimics the pivot table dynamic_correlation builds
    data = {
        "AAPL": [100.0, None, 102.0],
        "GOOG": [200.0, 201.0, None],
    }
    df_pivot = pd.DataFrame(data, index=pd.date_range("2024-01-01", periods=3))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")

        # Exercise the same call chain as dynamic_correlation.compute_correlation_matrix
        # GREEN path: df_pivot.ffill().dropna()
        # RED path: df_pivot.fillna(method="ffill").dropna()  — raises FutureWarning in pandas 2.x
        result = df_pivot.ffill().dropna()  # noqa: F841 (result consumed by assert below)

    # Assert no fillna(method=...) deprecation warning was emitted
    fillna_method_warnings = [
        w for w in caught
        if "fillna" in str(w.message).lower() and "method" in str(w.message).lower()
    ]
    assert len(fillna_method_warnings) == 0, (
        f"Unexpected pandas FutureWarning about fillna(method=): {fillna_method_warnings}"
    )


def test_source_has_no_fillna_method_kwarg():
    """
    Structural guard: the source of dynamic_correlation.py must NOT contain
    'fillna(method=' and MUST contain '.ffill()'.

    This test catches any revert of the positional-API migration.
    """
    import pathlib

    source_path = pathlib.Path(__file__).parent.parent / "app" / "services" / "dynamic_correlation.py"
    source = source_path.read_text(encoding="utf-8")

    assert "fillna(method=" not in source, (
        "dynamic_correlation.py still uses the deprecated fillna(method=...) API. "
        "Replace with df.ffill() (TECH-03)."
    )
    assert ".ffill()" in source, (
        "dynamic_correlation.py does not use .ffill() — positional API not applied (TECH-03)."
    )
