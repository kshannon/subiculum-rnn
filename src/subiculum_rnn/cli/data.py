"""data: synthetic trajectory datasets in the artifact store."""

from pathlib import Path

from ..experiments.registry import list_manifests
from ..store import Store, open_store
from ._output import emit, manifest_table
from ._parsers import add_dry_run, add_json, group, leaf
from ._stub import not_implemented

HELP = "synthetic trajectory datasets"
DESCRIPTION = ("A dataset is a registered artifact of generated trajectories: "
               "a directory holding manifest.yaml, trajectory blocks with "
               "derived kinematics, and validation reports.")


def register(groups) -> None:
    commands = group(groups, "data", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_datasets, example="subiculum-rnn data list")
    add_json(p)
    p.set_defaults(run=lambda a: list_datasets(open_store(a.store), as_json=a.json))

    p = leaf(commands, "inspect", inspect_dataset,
             example="subiculum-rnn data inspect ds_0001", stub=True)
    p.add_argument("dataset_id", metavar="<dataset>", help="dataset id, e.g. ds_0001")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_dataset(a.dataset_id, as_json=a.json))

    p = leaf(commands, "generate", generate,
             example="subiculum-rnn data generate --config configs/datasets/pilot.yaml",
             stub=True)
    p.add_argument("--config", required=True, metavar="<yaml>", type=Path,
                   help="dataset config: environment, agents, sessions, split")
    p.add_argument("--seed", type=int, default=None, metavar="N",
                   help="root seed (default: the config's)")
    add_dry_run(p)
    p.set_defaults(run=lambda a: generate(a.config, seed=a.seed, dry_run=a.dry_run))

    p = leaf(commands, "validate", validate,
             example="subiculum-rnn data validate ds_0001 --reference triple_t_reference.yaml",
             stub=True)
    p.add_argument("dataset_id", metavar="<dataset>", help="dataset id")
    p.add_argument("--reference", required=True, metavar="<file>", type=Path,
                   help="behavioral-statistics reference file, aggregate numbers only")
    add_dry_run(p)
    p.set_defaults(run=lambda a: validate(a.dataset_id, a.reference,
                                          dry_run=a.dry_run))

    p = leaf(commands, "stats", stats,
             example="subiculum-rnn data stats ds_0001 --json", stub=True)
    p.add_argument("dataset_id", metavar="<dataset>", help="dataset id")
    add_json(p)
    p.set_defaults(run=lambda a: stats(a.dataset_id, as_json=a.json))


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


def inspect_dataset(dataset_id: str, *, as_json: bool = False) -> int:
    """Describe one dataset: manifest, session and trial counts, split, validation.

    Reads: <store>/datasets/<dataset>/manifest.yaml and its validation reports.
    Writes: nothing.
    """
    return not_implemented("data inspect", "Commands")


def generate(config: Path, *, seed: int | None = None, dry_run: bool = False) -> int:
    """Build a synthetic dataset from an environment, agents and seeds.

    Reads: the dataset config and the environment and agent configs it names.
    Writes: <store>/datasets/<new id>/ with manifest, trajectories and derived
    kinematics; prints the existing id instead when the input hash matches.
    """
    return not_implemented("data generate", "Commands")


def validate(dataset_id: str, reference: Path, *, dry_run: bool = False) -> int:
    """Compare a dataset's behavioral statistics with a reference statistics file.

    Reads: the dataset and the reference file (aggregate numbers only).
    Writes: a validation report inside the dataset, recording the reference's checksum.
    """
    return not_implemented("data validate", "Commands")


def stats(dataset_id: str, *, as_json: bool = False) -> int:
    """Print a dataset's behavioral statistics; --json uses the reference-file structure.

    Reads: the dataset's trajectories and derived kinematics.
    Writes: nothing.
    """
    return not_implemented("data stats", "Commands")
