# subiculum-rnn

This repository contains a computational neuroscience research project investigating whether axis-of-travel-like representations can emerge spontaneously in a simple recurrent neural network (RNN) trained to predict an animal's future position during spatial navigation. The biological motivation is the literature describing axis-of-travel representations in the subiculum. The computational question is:
> If a simple recurrent network is trained only to predict future position from behavioral
> trajectory information, without being given an explicit axis-of-travel variable, does an
> axis-of-travel representation emerge in its hidden state?


## Quick start

```bash
# 1. Install pixi (one-time)
curl -fsSL https://pixi.sh/install.sh | bash

# 2. Clone
git clone git@github.com:kshannon/subiculum-rnn.git
cd subiculum-rnn

# 3. Install environment, dependencies and the project package (editable)
pixi install

# 4. Check it works
pixi run test
pixi run subiculum-rnn env list

# 5. Choose where artifacts live: artifacts/ in this checkout by default,
#    or a directory elsewhere, for example on an external drive
pixi run subiculum-rnn store init                       # default location
pixi run subiculum-rnn store init /Volumes/data/subiculum-rnn
export SUBICULUM_RNN_STORE=/Volumes/data/subiculum-rnn  # per machine, e.g. in your shell config
pixi run subiculum-rnn store inspect
```

## Using the project

The `subiculum-rnn` command orchestrates everything; the science lives in the
package under `src/subiculum_rnn/`. Commands are grouped by layer, and every
group and command has `--help` with what it reads, what it writes and an
example. The contract is [docs/cli/spec.md](docs/cli/spec.md).

```bash
pixi run subiculum-rnn --help                      # the groups: store, env, agent, data, model, analysis, experiment
pixi run subiculum-rnn store inspect               # where artifacts go, marker, counts, problems
pixi run subiculum-rnn env list                    # environment configs and geometry hashes
pixi run subiculum-rnn env inspect triple_t --json # one environment; the JSON is exactly what gets hashed
pixi run subiculum-rnn data list                   # registered datasets in the store
pixi run subiculum-rnn model list                  # registered models (model animals)
pixi run subiculum-rnn experiment list             # registered experiments (populations)
pixi run env-plot                                  # draw every environment to figures/environments.png
pixi run sim-smoke triple_t --seconds 120          # RatInABox random walk over an environment
pixi run note                                      # new lab notebook entry
```

Every command in the spec exists today. Those whose science is not yet built
(agents, data generation and validation, training, evaluation, hidden-state
recording, axis analysis, experiment runs) parse their full arguments, print
"not implemented" with their spec section, and exit with code 3. Exit codes:
0 success, 1 no command, 2 usage error or unusable store, 3 not implemented,
4 provenance mismatch.

Artifacts (datasets, models, experiments) are written only by this command,
into a store outside git: `--store DIR` for one run, the `SUBICULUM_RNN_STORE`
variable per machine, or `artifacts/` in the checkout by default. A store is a
directory with a `store.yaml` marker; commands refuse anything else, which
catches an unplugged drive. Each artifact carries a manifest recording the
configs and hashes, seeds, git commit and lockfile that produced it, so it is
regenerable and never modified in place.

## How synthetic data is generated

No recorded animal data lives in this repository or its store. Behavior is
synthetic: an environment config (triple-T track, open arena) fixes the
geometry; an agent config fixes a behavioral profile, meaning speed, turning
and dwell statistics and a goal policy; a dataset config names an environment,
agents, sessions and trials, seeds, and a split policy. `data generate` turns
that into trajectories of position and heading, stores velocity, speed and
angular velocity derived from them beside the raw arrays, and records every
config hash and seed in the dataset's manifest. `data validate` compares the
dataset's behavioral statistics against an aggregate reference-statistics file
and writes the report into the dataset. Only position reaches the RNN during
training; heading and kinematics exist for validation and controls. See
[docs/data_dictionary.md](docs/data_dictionary.md) for every field.

Principles every change must respect are in [AGENTS.md](AGENTS.md); status
and open decisions are in [docs/research_plan.md](docs/research_plan.md).

## Layout

```
configs/         declarative YAML: environments (built), datasets, models, training, experiments
src/subiculum_rnn/
  environments/  parametric geometry (triple-T, open arena, plus maze), content hashes, RatInABox adapter
  datasets/      trajectory schema and zarr IO; later generation, validation, versioning
  behavior/      agents, synthetic trajectories, behavioral statistics (not yet)
  models/        vanilla RNN, loss, training (not yet)
  analysis/      hidden states, axis tuning, controls, perturbations (not yet)
  store.py       the artifact store: resolution order, marker, layout, manifest scan
  cli/           the command line entry point: groups, stub table, real commands
tests/           unit, integration (RatInABox, zarr), scientific
docs/            research plan, data dictionary, reproduction, and per-feature spec, plan, tasks (docs/cli/)
artifacts/       the default store: datasets, models, experiments (git-ignored, regenerable)
labnotebook/     dated entries, `pixi run note`
```

## Replicability and Reproducibility

There is a complex history of these tertms and what they mean within different fields, especially with the rise of computation being essential to most research. Here I will use the National Academies<sup>1</sup> definition of these terms, which the Association for Computing Machinery<sup>2</sup> also agrees:

- **Replicability**: An attempt by a second researcher to replicate a previous study is an effort to determine whether applying the same methods to the same scientific question produces similar results.
- **Reproducibility**: obtaining consistent results using the same input data, computational methods, and conditions of analysis.


Synthetic data (generated with the RatInABox python library<sup>3</sup>), and open source data results should be reproducible. Results using your own collected recording data should be replicable to within some stated percision. Given the stochastic nature of machine learning methods, from data cleaning to pipeline construction to training and validation, it can be daunting to provide near 100% reproducibility, but it is a standard to strive for nonetheless.

To that end, this README provides all instructions needed to reproduce our synthetic data results. Instructions for reproducing results with open-source data and our own recorded data are provided in the project wiki.


| Requirement | How it's met |
|-------------|-------------|
| **Exact software versions** | `pixi.lock` pins every Python package, and its transitive dependencies, to a specific version |
| **Versioned data provenance** | Each synthetic dataset has a manifest with all generation parameters, seeds, the environment geometry hash and an ID |
| **Logged and versioned training runs** | Every dataset, model and experiment is a directory under `artifacts/` with a `manifest.yaml` recording config, seed, code commit and lockfile |
| **Cross-platform** | `pixi.toml` targets `linux-64`, `osx-arm64` |


## Citation

If you use this code, please cite the relevant papers (see project wiki for full reference list of papers and open source citable libraries).

**Cite this project**: `¯\_(ツ)_/¯` One Day!

---

1. National Academies of Sciences, Engineering, and Medicine. 2019. Reproducibility and Replicability in Science. Washington, DC: The National Academies Press. https://doi.org/10.17226/25303.
2. https://www.acm.org/publications/policies/artifact-review-and-badging-current
3. Tom M George, Mehul Rastogi, William de Cothi, Claudia Clopath, Kimberly Stachenfeld, Caswell Barry. "RatInABox, a toolkit for modelling locomotion and neuronal activity in continuous environments" (2024), eLife, https://doi.org/10.7554/eLife.85274 .
