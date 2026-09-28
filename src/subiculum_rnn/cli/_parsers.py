"""Parser helpers. A command's docstring is its help text: first line as the
summary, the whole docstring as the description, one example as the epilog.
"""

import argparse
import inspect


def group(groups, name: str, help: str, description: str):
    """Add a command group and return the action its commands register on."""
    parser = groups.add_parser(name, help=help, description=description)
    parser.set_defaults(group_parser=parser)
    return parser.add_subparsers(dest="command", metavar="<command>",
                                 title="commands")


def leaf(commands, name: str, func, *, example: str,
         stub: bool = False) -> argparse.ArgumentParser:
    """Add one command whose help comes from ``func``'s docstring."""
    doc = inspect.cleandoc(func.__doc__ or "")
    parser = commands.add_parser(
        name, help=doc.splitlines()[0] if doc else "", description=doc,
        epilog=f"example: {example}",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_defaults(stub=stub, example=example)
    return parser


def add_json(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true",
                        help="print the same data as JSON")


def add_dry_run(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true",
                        help="resolve inputs and print the id that would be "
                             "created; write nothing")
