"""CLI: every command runs, prints something useful, and exits cleanly."""

import json
from pathlib import Path

import pytest

from subiculum_rnn.cli import main


def test_no_command_prints_help(capsys):
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


def test_env_list_shows_every_config_with_its_hash(capsys):
    assert main(["env", "list"]) == 0
    out = capsys.readouterr().out
    for name in ("open_arena", "plus_maze", "triple_t", "triple_t_rot90"):
        assert name in out
    assert "hash" in out


def test_env_list_json_lists_every_config(capsys):
    assert main(["env", "list", "--json"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert [r["name"] for r in rows] == ["open_arena", "plus_maze", "triple_t", "triple_t_rot90"]
    assert all(len(r["hash"]) == 12 for r in rows)


def test_group_without_command_prints_group_help(capsys):
    assert main(["env"]) == 1
    assert "inspect" in capsys.readouterr().out


def test_env_inspect_reports_geometry(capsys):
    from subiculum_rnn.environments import load_environment
    spec = load_environment("triple_t")
    assert main(["env", "inspect", "triple_t"]) == 0
    out = capsys.readouterr().out
    assert spec.hash in out
    assert "ee" in out and "start" in out


def test_env_inspect_json_is_the_canonical_spec(capsys):
    assert main(["env", "inspect", "open_arena", "--json"]) == 0
    spec = json.loads(capsys.readouterr().out)
    assert spec["name"] == "open_arena"
    assert spec["kind"] == "circle"
    assert "hash" in spec


def test_env_inspect_unknown_name_fails_with_a_hint(capsys):
    assert main(["env", "inspect", "nope"]) != 0
    err = capsys.readouterr().err
    assert "nope" in err and "triple_t" in err


def _manifest(store: Path, kind: str, name: str, body: str):
    d = store / kind / name
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(body)


def test_store_init_then_inspect(tmp_path: Path, capsys):
    store = tmp_path / "s"
    assert main(["store", "init", str(store)]) == 0
    assert (store / "store.yaml").is_file()
    assert main(["--store", str(store), "store", "inspect"]) == 0
    out = capsys.readouterr().out
    assert str(store) in out and "datasets" in out
    assert main(["--store", str(store), "store", "inspect", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["counts"] == {"datasets": 0, "models": 0, "experiments": 0}
    assert report["source"] == "flag"


def test_store_init_defaults_to_the_environment_variable(tmp_path: Path, monkeypatch):
    store = tmp_path / "from-env"
    monkeypatch.setenv("SUBICULUM_RNN_STORE", str(store))
    assert main(["store", "init"]) == 0
    assert (store / "store.yaml").is_file()


def test_store_commands_fail_cleanly_without_a_marker(tmp_path: Path, capsys):
    missing = tmp_path / "unplugged"
    assert main(["--store", str(missing), "data", "list"]) == 2
    assert "store not found" in capsys.readouterr().err
    assert main(["--store", str(missing), "store", "inspect"]) == 2


def test_data_list_reports_empty_then_registered(tmp_path: Path, capsys):
    store = tmp_path / "s"
    assert main(["store", "init", str(store)]) == 0
    capsys.readouterr()
    root = ["--store", str(store)]
    assert main([*root, "data", "list"]) == 0
    out = capsys.readouterr().out
    assert "no datasets" in out.lower()
    assert str(store / "datasets") in out

    _manifest(store, "datasets", "ds_0001",
              "id: ds_0001\nenvironment: triple_t\ndescription: pilot\n")
    assert main([*root, "data", "list"]) == 0
    out = capsys.readouterr().out
    assert "ds_0001" in out and "triple_t" in out and "pilot" in out


def test_experiment_list_reports_empty_then_registered(tmp_path: Path, capsys):
    store = tmp_path / "s"
    assert main(["store", "init", str(store)]) == 0
    capsys.readouterr()
    root = ["--store", str(store)]
    assert main([*root, "experiment", "list"]) == 0
    assert "no experiments" in capsys.readouterr().out.lower()

    _manifest(store, "experiments", "exp_0001",
              "id: exp_0001\ndescription: first sweep\n")
    assert main([*root, "experiment", "list"]) == 0
    out = capsys.readouterr().out
    assert "exp_0001" in out and "first sweep" in out


def test_not_implemented_stub_exits_3_and_names_the_spec_section(capsys):
    from subiculum_rnn.cli._stub import not_implemented
    assert not_implemented("data generate", "Commands") == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "data generate" in captured.err
    assert "not implemented" in captured.err
    assert "docs/cli/spec.md" in captured.err and "Commands" in captured.err
