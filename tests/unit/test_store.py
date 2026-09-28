"""
The artifact store: resolution order, the marker, the layout and the scan.
"""

from pathlib import Path

import pytest
import yaml

from subiculum_rnn.paths import repo_root
from subiculum_rnn.store import (ENV_VAR, KINDS, STORE_VERSION, Store,
                                 StoreError, open_store, resolve_store)


def _artifact(store: Store, kind: str, name: str, declared_id: str) -> None:
    d = store.kind_dir(kind) / name
    d.mkdir()
    (d / "manifest.yaml").write_text(f"id: {declared_id}\n")


def test_resolution_order_is_flag_then_env_then_default(tmp_path: Path):
    flag, env = tmp_path / "flag", tmp_path / "env"
    chosen = resolve_store(str(flag), env={ENV_VAR: str(env)})
    assert (chosen.root, chosen.source) == (flag, "flag")
    chosen = resolve_store(None, env={ENV_VAR: str(env)})
    assert (chosen.root, chosen.source) == (env, "env")
    chosen = resolve_store(None, env={})
    assert (chosen.root, chosen.source) == (repo_root() / "artifacts", "default")


def test_init_creates_the_layout_and_the_marker(tmp_path: Path):
    store = Store(tmp_path / "s", "flag")
    marker = store.init()
    assert all(store.kind_dir(kind).is_dir() for kind in KINDS)
    assert set(marker) == {"store_version", "created", "hostname", "repo_commit",
                           "tool_version"}
    assert marker["store_version"] == STORE_VERSION
    assert store.init() == marker


def test_open_store_requires_a_marker(tmp_path: Path):
    missing = tmp_path / "missing"
    with pytest.raises(StoreError) as caught:
        open_store(str(missing), env={})
    assert str(missing) in str(caught.value) and "store init" in str(caught.value)

    bare = tmp_path / "bare"
    bare.mkdir()
    with pytest.raises(StoreError) as caught:
        open_store(str(bare), env={})
    assert str(bare) in str(caught.value) and "store init" in str(caught.value)


def test_open_store_refuses_a_marker_from_a_newer_tool(tmp_path: Path):
    store = Store(tmp_path / "s", "flag")
    store.init()
    store.marker.write_text(yaml.safe_dump({"store_version": STORE_VERSION + 1}))
    with pytest.raises(StoreError, match="store_version"):
        open_store(str(store.root), env={})


def test_survey_counts_artifacts_and_reports_problems(tmp_path: Path):
    store = Store(tmp_path / "s", "flag")
    store.init()
    _artifact(store, "datasets", "ds_0001", "ds_0001")
    _artifact(store, "datasets", "ds_0002", "ds_0009")
    (store.kind_dir("models") / "scratch").mkdir()
    counts, problems = store.survey()
    assert counts == {"datasets": 1, "models": 0, "experiments": 0}
    assert any("ds_0002" in p and "ds_0009" in p for p in problems)
    assert any("models/scratch" in p for p in problems)


def test_artifacts_skips_unmarked_directories_and_refuses_a_wrong_id(tmp_path: Path):
    store = Store(tmp_path / "s", "flag")
    store.init()
    _artifact(store, "datasets", "ds_0001", "ds_0001")
    (store.kind_dir("datasets") / "scratch").mkdir()
    assert [a.id for a in store.artifacts("datasets")] == ["ds_0001"]

    _artifact(store, "datasets", "ds_0002", "ds_0009")
    with pytest.raises(StoreError, match="ds_0009"):
        store.artifacts("datasets")
