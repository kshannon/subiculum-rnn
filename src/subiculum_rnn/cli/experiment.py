"""experiment: populations of model animals trained under one config."""

from ..experiments.registry import list_manifests
from ..paths import ProjectPaths
from ._output import emit, manifest_table
from ._parsers import add_json, group, leaf

HELP = "experiments: populations of models"
DESCRIPTION = ("An experiment is a registered artifact tying a population of "
               "models trained under one config to their shared manifest.")


def register(groups) -> None:
    commands = group(groups, "experiment", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_experiments,
             example="subiculum-rnn experiment list")
    add_json(p)
    p.set_defaults(run=lambda a: list_experiments(ProjectPaths.from_root(a.root),
                                                  as_json=a.json))


def list_experiments(paths: ProjectPaths, *, as_json: bool = False) -> int:
    """List registered experiments with config, model count and status.

    Reads: <store>/experiments/*/manifest.yaml.
    Writes: nothing.
    """
    entries = list_manifests(paths.experiments)
    if not entries:
        print(f"no experiments registered under {paths.experiments}")
        print("(an experiment is a directory holding manifest.yaml; "
              "training is not implemented yet)")
        return 0
    rows, text = manifest_table(entries)
    emit(rows, text, as_json=as_json)
    return 0
