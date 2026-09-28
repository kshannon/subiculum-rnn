"""Every command's own help example parses; list and inspect commands take
--json; artifact writers take --dry-run; every stub exits 3 when its example
is run."""

import argparse
import shlex

import pytest

from subiculum_rnn.cli import build_parser, main

WRITERS = {"generate", "validate", "train", "evaluate", "record-hidden", "axis",
           "run", "reproduce"}


def _subparsers(parser) -> dict:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return {}


def _leaves():
    for gname, gparser in _subparsers(build_parser()).items():
        for cname, cparser in _subparsers(gparser).items():
            yield f"{gname} {cname}", cname, cparser


LEAVES = list(_leaves())
IDS = [name for name, _, _ in LEAVES]


def _example_argv(parser) -> list[str]:
    example = parser.get_default("example")
    words = shlex.split(example)
    assert words[0] == "subiculum-rnn", example
    return words[1:]


@pytest.mark.parametrize("name,cname,parser", LEAVES, ids=IDS)
def test_example_parses_with_the_documented_arguments(name, cname, parser):
    build_parser().parse_args(_example_argv(parser))


@pytest.mark.parametrize("name,cname,parser", LEAVES, ids=IDS)
def test_shared_flags_follow_the_spec(name, cname, parser):
    options = parser._option_string_actions
    if cname in ("list", "inspect", "stats"):
        assert "--json" in options, f"{name} lacks --json"
    if cname in WRITERS:
        assert "--dry-run" in options, f"{name} lacks --dry-run"


STUBS = [(name, parser) for name, _, parser in LEAVES if parser.get_default("stub")]


@pytest.mark.parametrize("name,parser", STUBS, ids=[n for n, _ in STUBS])
def test_every_stub_exits_3_on_its_own_example(name, parser, capsys):
    assert main(_example_argv(parser)) == 3
    assert "not implemented" in capsys.readouterr().err


def test_the_stub_set_matches_the_spec_status():
    """env, store and the three list commands are real; everything else is a stub."""
    real = sorted(name for name, _, parser in LEAVES if not parser.get_default("stub"))
    assert real == ["data list", "env inspect", "env list", "experiment list",
                    "model list", "store init", "store inspect"]
