"""Output helpers shared by every group: tables, labeled lines, JSON, errors.

Data goes to stdout, errors to stderr. ``--json`` prints the same data the
human rendering was built from.
"""

import json
import sys


def table(rows: list[dict], columns: list[str]) -> str:
    """Fixed-width columns, header first, no trailing spaces."""
    cells = [[str(row.get(col, "")) for col in columns] for row in rows]
    widths = [max([len(col)] + [len(row[i]) for row in cells])
              for i, col in enumerate(columns)]

    def fmt(values):
        return "  ".join(v.ljust(w) for v, w in zip(values, widths)).rstrip()

    return "\n".join([fmt(columns)] + [fmt(row) for row in cells])


def lines(title: str, pairs: list[tuple[str, object]]) -> str:
    """A title line followed by aligned ``label  value`` lines."""
    width = max(len(label) for label, _ in pairs)
    return "\n".join([title] + [f"  {label.ljust(width)}  {value}"
                                for label, value in pairs])


def manifest_table(entries) -> tuple[list[dict], str]:
    """Rows and rendered table for registry entries. Optional columns appear
    when any manifest has them, so listing works before schemas are final."""
    optional = [c for c in ("environment", "dataset", "created", "description")
                if any(c in e.meta for e in entries)]
    rows = [{"id": e.id, **{c: e.meta.get(c, "") for c in optional}}
            for e in entries]
    return rows, table(rows, ["id", *optional])


def emit(data, text: str, *, as_json: bool) -> None:
    print(json.dumps(data, indent=2, default=str) if as_json else text)


def fail(message: str, code: int = 2) -> int:
    print(f"error: {message}", file=sys.stderr)
    return code
