"""analysis: hidden-state recording and axis-of-travel tuning on frozen models."""

from pathlib import Path

from ._parsers import add_dry_run, group, leaf
from ._stub import not_implemented

HELP = "hidden states and axis-of-travel analysis"
DESCRIPTION = ("Analysis runs on frozen models. Recording pushes standardized "
               "trajectories through a checkpoint and saves hidden states; axis "
               "measures axis-of-travel tuning per unit, with controls. Both "
               "write inside the model's directory.")


def register(groups) -> None:
    commands = group(groups, "analysis", HELP, DESCRIPTION)

    p = leaf(commands, "record-hidden", record_hidden,
             example="subiculum-rnn analysis record-hidden rnn_000001 --dataset ds_0001",
             stub=True)
    p.add_argument("model_id", metavar="<model>", help="model id")
    p.add_argument("--dataset", required=True, metavar="<id>",
                   help="dataset whose standardized trajectories are replayed")
    p.add_argument("--checkpoint", default=None, metavar="<name>",
                   help="checkpoint name (default: best validation)")
    add_dry_run(p)
    p.set_defaults(run=lambda a: record_hidden(a.model_id, a.dataset,
                                               checkpoint=a.checkpoint,
                                               dry_run=a.dry_run))

    p = leaf(commands, "axis", axis,
             example="subiculum-rnn analysis axis rnn_000001 --dataset ds_0001",
             stub=True)
    p.add_argument("model_id", metavar="<model>", help="model id")
    p.add_argument("--dataset", required=True, metavar="<id>",
                   help="dataset whose recording is analyzed")
    p.add_argument("--config", default=None, metavar="<yaml>", type=Path,
                   help="analysis config (default: configs/analysis/axis.yaml)")
    add_dry_run(p)
    p.set_defaults(run=lambda a: axis(a.model_id, a.dataset, config=a.config,
                                      dry_run=a.dry_run))


def record_hidden(model_id: str, dataset_id: str, *, checkpoint: str | None = None,
                  dry_run: bool = False) -> int:
    """Run standardized trajectories through a frozen checkpoint; save hidden states.

    Reads: the model checkpoint and the dataset's trajectories.
    Writes: a recording inside <store>/models/<model>/recordings/.
    """
    return not_implemented("analysis record-hidden", "Commands")


def axis(model_id: str, dataset_id: str, *, config: Path | None = None,
         dry_run: bool = False) -> int:
    """Measure axis-of-travel tuning per hidden unit, with controls.

    Reads: the recording for the dataset and the analysis config.
    Writes: results inside <store>/models/<model>/analysis/.
    """
    return not_implemented("analysis axis", "Commands")
