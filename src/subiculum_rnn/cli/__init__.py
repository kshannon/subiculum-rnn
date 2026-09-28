"""Command-line entry point: ``subiculum-rnn <group> <command>``.

Orchestration only. Each group is a module in this package exposing
``register(groups)``; each command is a plain function with explicit
parameters that returns an exit code. Nothing here knows how the science
works; see docs/cli/spec.md for the contract.

Exit codes: 0 success, 1 no command, 2 usage error, unknown name or unusable
store, 3 not implemented, 4 provenance mismatch.
"""

import argparse

from .. import __version__
from ..store import ENV_VAR, StoreError
from . import agent, data, env, experiment, model
from . import store as store_group
from ._output import fail

GROUPS = (store_group, env, agent, data, model, experiment)

DESCRIPTION = "Axis-of-travel emergence in position-predicting RNNs."
EPILOG = (f"Artifacts live in a store chosen by --store, then ${ENV_VAR}, then "
          "artifacts/ in this checkout. Exit codes: 0 success, 1 no command, "
          "2 usage error or unusable store, 3 not implemented, "
          "4 provenance mismatch.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="subiculum-rnn", description=DESCRIPTION,
                                     epilog=EPILOG)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--store", metavar="DIR", default=None,
                        help=f"artifact store for this run (default: ${ENV_VAR}, "
                             "else artifacts/ in the checkout)")
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
    try:
        return run(args)
    except StoreError as e:
        return fail(str(e))
