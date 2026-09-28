"""data: synthetic trajectory datasets in the artifact store."""

from ..experiments.registry import list_manifests
from ..store import Store, open_store
from ._output import emit, manifest_table
from ._parsers import add_json, group, leaf

HELP = "synthetic trajectory datasets"
DESCRIPTION = ("A dataset is a registered artifact of generated trajectories: "
               "a directory holding manifest.yaml, trajectory blocks with "
               "derived kinematics, and validation reports.")


def register(groups) -> None:
    commands = group(groups, "data", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_datasets, example="subiculum-rnn data list")
    add_json(p)
    p.set_defaults(run=lambda a: list_datasets(open_store(a.store), as_json=a.json))


def list_datasets(store: Store, *, as_json: bool = False) -> int:
    """List registered datasets with environment, agents, input hash and created.

    Reads: <store>/datasets/*/manifest.yaml.
    Writes: nothing.
    """
    directory = store.kind_dir("datasets")
    entries = list_manifests(directory)
    if not entries:
        print(f"no datasets registered under {directory}")
        print("(a dataset is a directory holding manifest.yaml; "
              "`data generate` is not implemented yet)")
        return 0
    rows, text = manifest_table(entries)
    emit(rows, text, as_json=as_json)
    return 0
