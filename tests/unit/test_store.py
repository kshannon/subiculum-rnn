"""The artifact store: resolution order, the marker, layout, and checks."""

from pathlib import Path

import pytest
import yaml

from subiculum_rnn.store import (ENV_VAR, KINDS, STORE_VERSION, Store,
                                 StoreError, default_store_root, open_store,
                                 resolve_store)


def test_resolution_order_is_flag_then_env_then_default(tmp_path: Path):
    flag, env = tmp_path / "flag", tmp_path / "env"
    chosen = resolve_store(str(flag), env={ENV_VAR: str(env)})
    assert (chosen.root, chosen.source) == (flag, "flag")
    chosen = resolve_store(None, env={ENV_VAR: str(env)})
    assert (chosen.root, chosen.source) == (env, "env")
    chosen = resolve_store(None, env={})
    assert (chosen.root, chosen.source) == (default_store_root(), "default")
    assert default_store_root().name == "artifacts"


def test_init_creates_layout_and_marker(tmp_path: Path):
    store = Store(tmp_path / "s", source="flag")
    marker = store.init()
    assert store.marker.is_file()
    assert all(store.kind_dir(kind).is_dir() for kind in KINDS)
    assert marker["store_version"] == STORE_VERSION
    assert {"created", "hostname", "repo_commit", "tool_version"} <= set(marker)
    assert store.init() == marker, "a second init must not rewrite the marker"


def test_open_store_requires_a_marker(tmp_path: Path):
    with pytest.raises(StoreError, match="store not found"):
        open_store(str(tmp_path / "missing"), env={})
    (tmp_path / "bare").mkdir()
    with pytest.raises(StoreError, match="store init"):
        open_store(str(tmp_path / "bare"), env={})


def test_open_store_refuses_a_newer_marker(tmp_path: Path):
    store = Store(tmp_path / "s", source="flag")
    store.init()
    store.marker.write_text(yaml.safe_dump({"store_version": STORE_VERSION + 1}))
    with pytest.raises(StoreError, match="version"):
        open_store(str(store.root), env={})


def _artifact(store: Store, kind: str, name: str, declared_id: str) -> None:
    d = store.kind_dir(kind) / name
    d.mkdir()
    (d / "manifest.yaml").write_text(f"id: {declared_id}\n")


def test_check_reports_problems_and_counts_valid_artifacts(tmp_path: Path):
    store = Store(tmp_path / "s", source="flag")
    store.init()
    _artifact(store, "datasets", "ds_0001", "ds_0001")
    _artifact(store, "datasets", "ds_0002", "ds_0009")
    (store.kind_dir("models") / "scratch").mkdir()
    problems = store.check()
    assert any("ds_0002" in p and "ds_0009" in p for p in problems)
    assert any("scratch" in p for p in problems)
    assert store.counts() == {"datasets": 1, "models": 0, "experiments": 0}
