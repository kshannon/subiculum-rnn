"""Command-line entry point: ``subiculum-rnn <group> <command>``.

Orchestration only. Each group is a module in this package exposing
``register(groups)``; each command is a plain function with explicit
parameters that returns an exit code. Nothing here knows how the science
works; see docs/cli/spec.md for the contract.
"""

import argparse

from .. import __version__
from . import data, env, experiment

GROUPS = (env, data, experiment)

DESCRIPTION = "Axis-of-travel emergence in position-predicting RNNs."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="subiculum-rnn", description=DESCRIPTION)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--root", metavar="DIR", default=None,
                        help="project tree holding configs/ and artifacts/ "
                             "(default: this checkout)")
    groups = parser.add_subparsers(dest="group", metavar="<group>", title="groups")
    for module in GROUPS:
        module.register(groups)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    run = getattr(args, "run", None)
    if run is None:
        getattr(args, "group_parser", parser).print_help()
        return 1
    return run(args)
