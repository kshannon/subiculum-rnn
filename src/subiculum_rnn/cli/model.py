"""model: trained model animals in the artifact store."""

from pathlib import Path

from ..experiments.registry import list_manifests
from ..store import Store, open_store
from ._output import emit, manifest_table
from ._parsers import add_dry_run, add_json, group, leaf
from ._stub import not_implemented

HELP = "trained models (model animals)"
DESCRIPTION = ("A model is one complete training run, a model animal: a "
               "registered artifact holding manifest.yaml, checkpoints, "
               "evaluations, hidden-state recordings and analysis results.")


def register(groups) -> None:
    commands = group(groups, "model", HELP, DESCRIPTION)

    p = leaf(commands, "list", list_models, example="subiculum-rnn model list")
    add_json(p)
    p.set_defaults(run=lambda a: list_models(open_store(a.store), as_json=a.json))

    p = leaf(commands, "inspect", inspect_model,
             example="subiculum-rnn model inspect rnn_000001", stub=True)
    p.add_argument("model_id", metavar="<model>", help="model id, e.g. rnn_000001")
    add_json(p)
    p.set_defaults(run=lambda a: inspect_model(a.model_id, as_json=a.json))

    p = leaf(commands, "train", train,
             example="subiculum-rnn model train --model-config configs/models/small.yaml "
                     "--training-config configs/training/baseline.yaml "
                     "--dataset ds_0001 --seed 1", stub=True)
    p.add_argument("--model-config", required=True, metavar="<yaml>", type=Path,
                   help="architecture config: hidden size, layers, nonlinearity")
    p.add_argument("--training-config", required=True, metavar="<yaml>", type=Path,
                   help="optimizer, learning rate, batch size, sequence length, stopping")
    p.add_argument("--dataset", required=True, metavar="<id>", help="dataset id")
    p.add_argument("--seed", required=True, type=int, metavar="N", help="random seed")
    add_dry_run(p)
    p.set_defaults(run=lambda a: train(a.model_config, a.training_config, a.dataset,
                                       a.seed, dry_run=a.dry_run))

    p = leaf(commands, "evaluate", evaluate,
             example="subiculum-rnn model evaluate rnn_000001 --dataset ds_0001",
             stub=True)
    p.add_argument("model_id", metavar="<model>", help="model id")
    p.add_argument("--dataset", required=True, metavar="<id>", help="dataset id")
    add_dry_run(p)
    p.set_defaults(run=lambda a: evaluate(a.model_id, a.dataset, dry_run=a.dry_run))


def list_models(store: Store, *, as_json: bool = False) -> int:
    """List registered models with dataset, config, seed, status and best loss.

    Reads: <store>/models/*/manifest.yaml.
    Writes: nothing.
    """
    directory = store.kind_dir("models")
    entries = list_manifests(directory)
    if not entries:
        print(f"no models registered under {directory}")
        print("(a model is a directory holding manifest.yaml; "
              "`model train` is not implemented yet)")
        return 0
    rows, text = manifest_table(entries)
    emit(rows, text, as_json=as_json)
    return 0


def inspect_model(model_id: str, *, as_json: bool = False) -> int:
    """Describe one model: manifest, checkpoints, metrics and hash checks.

    Reads: <store>/models/<model>/manifest.yaml and what it points to.
    Writes: nothing.
    """
    return not_implemented("model inspect", "Commands")


def train(model_config: Path, training_config: Path, dataset_id: str, seed: int,
          *, dry_run: bool = False) -> int:
    """Train one model animal; refuse on hash drift, reuse on an input-hash match.

    Reads: the model and training configs and the dataset, checking its recorded
    environment and agent hashes against the current configs.
    Writes: <store>/models/<new id>/ with manifest and checkpoints.
    """
    return not_implemented("model train", "Commands")


def evaluate(model_id: str, dataset_id: str, *, dry_run: bool = False) -> int:
    """Evaluate a frozen model on a dataset's held-out split.

    Reads: the model's best checkpoint and the dataset.
    Writes: metrics inside <store>/models/<model>/evaluations/.
    """
    return not_implemented("model evaluate", "Commands")
