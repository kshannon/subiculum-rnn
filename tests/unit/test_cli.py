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


def _manifest(root: Path, kind: str, name: str, body: str):
    d = root / "artifacts" / kind / name
    d.mkdir(parents=True)
    (d / "manifest.yaml").write_text(body)


def test_data_list_reports_empty_then_registered(tmp_path: Path, capsys):
    root = ["--root", str(tmp_path)]
    assert main([*root, "data", "list"]) == 0
    out = capsys.readouterr().out
    assert "no datasets" in out.lower()
    assert str(tmp_path / "artifacts" / "datasets") in out

    _manifest(tmp_path, "datasets", "ds_0001",
              "id: ds_0001\nenvironment: triple_t\ndescription: pilot\n")
    assert main([*root, "data", "list"]) == 0
    out = capsys.readouterr().out
    assert "ds_0001" in out and "triple_t" in out and "pilot" in out


def test_experiment_list_reports_empty_then_registered(tmp_path: Path, capsys):
    root = ["--root", str(tmp_path)]
    assert main([*root, "experiment", "list"]) == 0
    assert "no experiments" in capsys.readouterr().out.lower()

    _manifest(tmp_path, "experiments", "exp_0001",
              "id: exp_0001\ndescription: first sweep\n")
    assert main([*root, "experiment", "list"]) == 0
    out = capsys.readouterr().out
    assert "exp_0001" in out and "first sweep" in out
