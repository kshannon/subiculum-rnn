"""store: the artifact store that holds datasets, models and experiments."""

from pathlib import Path

from ..store import ENV_VAR, Store, StoreError, resolve_store
from ._output import emit, fail, lines
from ._parsers import add_json, group, leaf

HELP = "the artifact store"
DESCRIPTION = ("Artifacts live in a store outside git: a directory with a "
               "store.yaml marker and one directory per kind. It is chosen by "
               f"--store, then the {ENV_VAR} variable, then artifacts/ in this "
               "checkout.")

CHOSEN_BY = {"flag": "--store", "env": f"${ENV_VAR}",
             "default": "default, artifacts/ in the checkout",
             "argument": "argument"}


def register(groups) -> None:
    commands = group(groups, "store", HELP, DESCRIPTION)

    p = leaf(commands, "init", init_store,
             example="subiculum-rnn store init /Volumes/ratdata/subiculum-rnn")
    p.add_argument("dir", metavar="DIR", nargs="?", default=None,
                   help="directory to initialize (default: the resolved store)")
    p.set_defaults(run=lambda a: init_store(
        Store(Path(a.dir).expanduser(), "argument") if a.dir
        else resolve_store(a.store)))

    p = leaf(commands, "inspect", inspect_store,
             example="subiculum-rnn store inspect --json")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_store(resolve_store(a.store),
                                               as_json=a.json))


def init_store(store: Store) -> int:
    """Create the store layout and its store.yaml marker.

    Reads: nothing.
    Writes: <store>/store.yaml plus datasets/, models/ and experiments/.
    An already initialized store is left untouched.
    """
    existed = store.initialized
    try:
        marker = store.init()
    except (StoreError, OSError) as e:
        return fail(str(e))
    state = "already initialized" if existed else "initialized"
    print(f"{state} store at {store.root} (version {marker['store_version']})")
    return 0


def inspect_store(store: Store, *, as_json: bool = False) -> int:
    """Show the resolved store: path, how it was chosen, marker, counts, problems.

    Reads: <store>/store.yaml and every manifest in the store.
    Writes: nothing.
    """
    try:
        marker = store.read_marker()
    except StoreError as e:
        return fail(str(e))
    counts, problems = store.counts(), store.check()
    report = {"path": str(store.root), "source": store.source,
              "marker": marker, "counts": counts, "problems": problems}
    pairs = [("path", store.root), ("chosen by", CHOSEN_BY[store.source])]
    pairs += [(key.replace("_", " "), value) for key, value in marker.items()]
    pairs += [(kind, count) for kind, count in counts.items()]
    pairs.append(("problems", "none" if not problems else "; ".join(problems)))
    emit(report, lines(f"store {store.root}", pairs), as_json=as_json)
    return 0
