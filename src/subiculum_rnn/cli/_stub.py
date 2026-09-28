"""Stubs: commands whose contract exists before their implementation. A stub
parses its full argument list, then reports here and exits 3."""

import sys

SPEC = "docs/cli/spec.md"


def not_implemented(command: str, section: str) -> int:
    print(f"{command}: not implemented; see {SPEC}, section {section!r}",
          file=sys.stderr)
    return 3
