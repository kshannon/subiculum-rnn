"""Help contract: the root lists groups and exit codes, every group has a
description and commands, every command says what it reads and writes and
shows one example that starts with its own name."""

import argparse

import pytest

from subiculum_rnn.cli import build_parser


def _subparsers(parser) -> dict:
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            return action.choices
    return {}


def _leaves():
    root = build_parser()
    for gname, gparser in _subparsers(root).items():
        for cname, cparser in _subparsers(gparser).items():
            yield f"{gname} {cname}", cparser


LEAVES = list(_leaves())


def test_root_help_lists_every_group_and_the_exit_codes():
    root = build_parser()
    text = root.format_help()
    assert all(name in text for name in _subparsers(root))
    assert "Exit codes" in text


def test_every_group_has_a_description_and_commands():
    for name, gparser in _subparsers(build_parser()).items():
        assert gparser.description, f"{name} has no description"
        assert _subparsers(gparser), f"{name} has no commands"


@pytest.mark.parametrize("name,parser", LEAVES, ids=[n for n, _ in LEAVES])
def test_command_help_states_reads_writes_and_an_example(name, parser):
    assert "Reads:" in parser.description and "Writes:" in parser.description
    assert parser.epilog.startswith(f"example: subiculum-rnn {name}")
