"""data: synthetic trajectory datasets in the artifact store."""

from ..experiments.registry import list_manifests
from ..paths import ProjectPaths
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
    p.set_defaults(run=lambda a: list_datasets(ProjectPaths.from_root(a.root),
                                               as_json=a.json))


def list_datasets(paths: ProjectPaths, *, as_json: bool = False) -> int:
    """List registered datasets with environment, agents, input hash and created.

    Reads: <store>/datasets/*/manifest.yaml.
    Writes: nothing.
    """
    entries = list_manifests(paths.datasets)
    if not entries:
        print(f"no datasets registered under {paths.datasets}")
        print("(a dataset is a directory holding manifest.yaml; "
              "`data generate` is not implemented yet)")
        return 0
    rows, text = manifest_table(entries)
    emit(rows, text, as_json=as_json)
    return 0
