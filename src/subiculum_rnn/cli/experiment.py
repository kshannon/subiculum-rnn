"""experiment: populations of model animals trained under one config."""

from pathlib import Path

from ..experiments.registry import list_manifests
from ..store import Store, open_store
from ._output import emit, manifest_table
from ._parsers import add_dry_run, add_json, group, leaf
from ._stub import not_implemented

HELP = "experiments: populations of models"
DESCRIPTION = ("An experiment is a registered artifact tying a population of "
               "models trained under one config to their shared manifest. "
               "Populations, not single runs, answer the question.")


def register(groups) -> None:
    commands = group(groups, "experiment", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_experiments,
             example="subiculum-rnn experiment list")
    add_json(p)
    p.set_defaults(run=lambda a: list_experiments(open_store(a.store),
                                                  as_json=a.json))

    p = leaf(commands, "inspect", inspect_experiment,
             example="subiculum-rnn experiment inspect exp_0001", stub=True)
    p.add_argument("experiment_id", metavar="<experiment>",
                   help="experiment id, e.g. exp_0001")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_experiment(a.experiment_id,
                                                    as_json=a.json))

    p = leaf(commands, "run", run,
             example="subiculum-rnn experiment run --config configs/experiments/seed_sweep.yaml",
             stub=True)
    p.add_argument("--config", required=True, metavar="<yaml>", type=Path,
                   help="experiment config: dataset, model and training configs, seeds")
    add_dry_run(p)
    p.set_defaults(run=lambda a: run(a.config, dry_run=a.dry_run))

    p = leaf(commands, "reproduce", reproduce,
             example="subiculum-rnn experiment reproduce exp_0001", stub=True)
    p.add_argument("experiment_id", metavar="<experiment>", help="experiment id")
    add_dry_run(p)
    p.set_defaults(run=lambda a: reproduce(a.experiment_id, dry_run=a.dry_run))


def list_experiments(store: Store, *, as_json: bool = False) -> int:
    """List registered experiments with config, model count and status.

    Reads: <store>/experiments/*/manifest.yaml.
    Writes: nothing.
    """
    directory = store.kind_dir("experiments")
    entries = list_manifests(directory)
    if not entries:
        print(f"no experiments registered under {directory}")
        print("(an experiment is a directory holding manifest.yaml; "
              "`experiment run` is not implemented yet)")
        return 0
    rows, text = manifest_table(entries)
    emit(rows, text, as_json=as_json)
    return 0


def inspect_experiment(experiment_id: str, *, as_json: bool = False) -> int:
    """Describe one experiment: its members with status, and results.

    Reads: <store>/experiments/<experiment>/manifest.yaml and member manifests.
    Writes: nothing.
    """
    return not_implemented("experiment inspect", "Commands")


def run(config: Path, *, dry_run: bool = False) -> int:
    """Train a population from one config, adopting members that already exist.

    Reads: the experiment config and the dataset, model and training configs it names.
    Writes: <store>/experiments/<new id>/ and one model per seed not already present.
    """
    return not_implemented("experiment run", "Commands")


def reproduce(experiment_id: str, *, dry_run: bool = False) -> int:
    """Verify commit, lockfile and hashes, re-run into a linked experiment, compare.

    Reads: the experiment manifest, current configs, git commit and lockfile.
    Writes: a new experiment linked to the original, plus the drift and comparison report.
    """
    return not_implemented("experiment reproduce", "Commands")
