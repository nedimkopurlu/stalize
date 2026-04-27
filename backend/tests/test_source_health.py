from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import time

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.services import source_health


def test_concurrent_source_updates_keep_all_sources(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    state_file = runtime_dir / "source_health.json"

    monkeypatch.setattr(source_health, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(source_health, "STATE_FILE", state_file)

    original_write_state = source_health._write_state

    def delayed_write_state(state):
        time.sleep(0.02)
        original_write_state(state)

    monkeypatch.setattr(source_health, "_write_state", delayed_write_state)

    barrier = Barrier(2)

    def write_source(name: str):
        barrier.wait()
        source_health.record_source_success(name, detail={"stored_count": 1})

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(write_source, "kap"),
            executor.submit(write_source, "tcmb"),
        ]
        for future in futures:
            future.result()

    payload = source_health.get_all_source_health()

    assert set(payload) == {"kap", "tcmb"}
    assert payload["kap"]["detail"]["stored_count"] == 1
    assert payload["tcmb"]["detail"]["stored_count"] == 1


def test_failure_without_detail_preserves_last_success_detail(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    state_file = runtime_dir / "source_health.json"

    monkeypatch.setattr(source_health, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(source_health, "STATE_FILE", state_file)

    source_health.record_source_success("kap", detail={"stored_count": 4, "fetched_count": 5})
    source_health.record_source_failure("kap", "temporary fetch error")

    payload = source_health.get_all_source_health()
    assert payload["kap"]["detail"] == {"stored_count": 4, "fetched_count": 5}
    assert payload["kap"]["last_error"] == "temporary fetch error"
    assert [item["status"] for item in payload["kap"]["history"]] == ["success", "failure"]


def test_runtime_summary_tracks_success_rate_and_failure_streak(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    state_file = runtime_dir / "source_health.json"

    monkeypatch.setattr(source_health, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(source_health, "STATE_FILE", state_file)

    source_health.record_source_success("tcmb", detail={"stored_count": 2})
    source_health.record_source_failure("tcmb", "first failure")
    source_health.record_source_failure("tcmb", "second failure")

    payload = source_health.get_all_source_health()
    summary = source_health.summarize_source_runtime(payload["tcmb"])

    assert summary["last_outcome"] == "failure"
    assert summary["consecutive_failures"] == 2
    assert summary["success_rate"] == 33.3
    assert summary["recent_outcomes"] == ["success", "failure", "failure"]
    assert summary["history_size"] == 3


def test_source_health_history_reads_from_db_ledger(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    state_file = runtime_dir / "source_health.json"

    monkeypatch.setattr(source_health, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(source_health, "STATE_FILE", state_file)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[source_health.SourceHealthRun.__table__])
    monkeypatch.setattr(source_health, "sync_engine", engine)

    source_health.record_source_success("kap", detail={"stored_count": 3})
    source_health.record_source_failure("kap", "temporary fetch error", detail={"attempt": 2})

    history = source_health.get_source_health_history(source_key="kap", limit=10)

    assert len(history) == 2
    assert history[0]["status"] == "failure"
    assert history[0]["error"] == "temporary fetch error"
    assert history[1]["status"] == "success"
    assert history[1]["detail"]["stored_count"] == 3


def test_source_health_ledger_snapshot_summarizes_recent_runs(tmp_path, monkeypatch):
    runtime_dir = tmp_path / "runtime"
    state_file = runtime_dir / "source_health.json"

    monkeypatch.setattr(source_health, "RUNTIME_DIR", runtime_dir)
    monkeypatch.setattr(source_health, "STATE_FILE", state_file)

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine, tables=[source_health.SourceHealthRun.__table__])
    monkeypatch.setattr(source_health, "sync_engine", engine)

    source_health.record_source_failure("kap", "timeout")
    source_health.record_source_success("kap", detail={"stored_count": 4})
    source_health.record_source_failure("kap", "rss parse error")

    snapshot = source_health.get_source_health_ledger_snapshot(source_keys=["kap"], per_source_limit=5)

    assert snapshot["kap"]["last_outcome"] == "failure"
    assert snapshot["kap"]["consecutive_failures"] == 1
    assert snapshot["kap"]["success_rate"] == 33.3
    assert snapshot["kap"]["trend"] == "deteriorating"
    assert snapshot["kap"]["latest_error"] == "rss parse error"
    assert [item["status"] for item in snapshot["kap"]["recent_runs"]] == ["failure", "success", "failure"]
