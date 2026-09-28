# Reproduction

## Setup

    curl -fsSL https://pixi.sh/install.sh | bash   # once
    git clone git@github.com:kshannon/subiculum-rnn.git
    cd subiculum-rnn
    pixi install

`pixi install` pins every package from `pixi.lock` and installs the project
package in editable mode, which provides the `subiculum-rnn` command.

## Commands

    pixi run test                                  # unit + integration tests
    pixi run test-cov                              # with coverage
    pixi run subiculum-rnn --help                  # groups; add --help to any group or command
    pixi run subiculum-rnn store init [DIR]        # create a store (default: the resolved one)
    pixi run subiculum-rnn store inspect [--json]  # resolved path, marker, counts, problems
    pixi run subiculum-rnn env list [--json]       # environment configs and hashes
    pixi run subiculum-rnn env inspect triple_t [--json]
    pixi run subiculum-rnn data list               # registered datasets
    pixi run subiculum-rnn model list              # registered models
    pixi run subiculum-rnn experiment list         # registered experiments
    pixi run env-plot                              # figures/environments.png
    pixi run sim-smoke triple_t --seconds 120 --seed 0

`python -m subiculum_rnn` is equivalent to `subiculum-rnn`. The store is
chosen by `--store DIR`, else the `SUBICULUM_RNN_STORE` variable, else
`artifacts/` in the checkout; configs always come from the checkout. Commands
not yet implemented exit 3; the full contract is [cli/spec.md](cli/spec.md).

## Versioning layers

These are recorded separately and never conflated:

| layer | identified by |
|---|---|
| code | git commit |
| environment (software) | `pixi.lock` |
| environment (geometry) | config name plus `EnvSpec.hash` |
| dataset | dataset id and manifest |
| model configuration | config file under `configs/models/` |
| model instance | model id, seed, checkpoint |
| analysis | analysis config plus code commit |

## What is tracked in git

Code, configs, docs, tests, the lab notebook, `pixi.lock`. Not tracked: the
store (`artifacts/` or wherever `SUBICULUM_RNN_STORE` points), `figures/`,
checkpoints, anything regenerable from configs, code and seeds.
