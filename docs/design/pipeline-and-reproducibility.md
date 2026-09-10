---
title: RNN pipeline, reproducibility, and stopping criteria
date: 2026-09-10
created: 2026-09-10T17:05:00-0700
status: design — pre-implementation
tags: [design, pipeline, reproducibility, stopping, latent-space]
---

# RNN pipeline, reproducibility, and stopping criteria

**Status:** design exploration written before any pipeline code exists. Everything
below is a proposal. Numbers (budgets, checkpoint cadence, seed counts, thresholds)
are placeholders to be calibrated from pilot runs and then revised *here*, so this
document stays the record of what was decided and why.

## Summary

1. **Pipeline.** Five stages — data generation/ingestion, dataset assembly, model,
   training, evaluation/analysis — each a pure function of *(config, upstream
   artifact ID)*, so any number in a figure traces back to exact inputs. This maps
   onto the `data-synthetic` / `train` / `test` tasks already declared in
   `pixi.toml`.
2. **Reproducibility.** Every run is a self-describing directory: a manifest (git
   SHA, lock-file hash, resolved config, dataset content hash, hardware, seeds), the
   *initial* weights, dense checkpoints carrying optimizer/scheduler/RNG state,
   local metric logs (Weights & Biases mirrors them, never replaces them), and
   hidden-state dumps on a frozen probe set. Seeds are split into independent
   streams (data, init, shuffling). Bitwise reproducibility is claimed only within
   a (hardware, lock file) pair; the *scientific* claim is statistical
   replicability across seeds.
3. **Stopping.** Decouple *when to stop spending compute* from *which checkpoint to
   analyze*. Compute stops at a fixed step budget, identical across seeds and
   conditions, calibrated from pilots (roughly 3× the time-to-plateau of the
   validation task error). Checkpoints are selected post hoc by a pre-registered,
   task-side rule. Axis-of-travel and spatial-analogy metrics are **monitored at
   every checkpoint but never used for stopping or selection** — otherwise the
   emergence claim becomes an artifact of the procedure.
4. **Latent-space readiness.** A versioned probe battery that dissociates axis of
   travel from location and from direction; checkpoint 0 as the null model;
   per-checkpoint hidden-state dumps as labeled arrays; cross-seed geometry
   comparison under identical budgets.

---

## 1. Framing

**The model.** A recurrent network whose inputs are region-tagged population
activity — head-direction cells standing in for ADn, place cells for CA1, and an
RSC-like population (egocentric boundary and/or conjunctive cells) — and whose
readouts predict the animal's position and head direction Δ time-bins ahead. The
hidden state is then interrogated for axis-of-travel tuning (Olson, Tongprasearth
& Nitz, 2017) and spatial-analogy representations.

**Three questions the pipeline must answer cleanly:**

- *Emergence.* Does axis-of-travel coding appear in the hidden state, relative to
  the untrained network?
- *Dependence.* Which inputs and task settings does it depend on? (Ablate ADn, CA1,
  or RSC inputs; vary the prediction horizon Δ; vary the recurrent cell type and
  regularizers.)
- *Replicability.* Does the *geometry* of the representation replicate across seeds,
  even though individual units will not?

**Reproducibility targets**, using the README's National Academies definitions:

| Claim | Scope | How it is demonstrated |
|---|---|---|
| Reproducible | same hardware class + same `pixi.lock` + same seeds | re-running from a manifest reproduces metrics and weights bitwise, or to a float tolerance recorded in the manifest |
| Replicable | different seeds, data draws, or machines | the effect (fraction of axis-tuned units, decoding accuracy, geometry similarity, …) falls within a stated tolerance across N runs |

A single-seed result is an anecdote. Multi-seed runs are the unit of evidence, and
everything in sections 3–4 is designed so that multi-seed comparisons are not
confounded by the training procedure itself.

---

## 2. Pipeline

| Stage | Input | Output | Config group | Identity |
|---|---|---|---|---|
| 1. Data generation / ingestion | RatInABox config, or DANDI asset, or own recording | zarr store + `dataset.yaml` | `data/` | `dataset_id` = content hash |
| 2. Dataset assembly | dataset + split spec | windowed sequences, split manifest, normalization stats | `data/` | split manifest hash |
| 3. Model | architecture config | instantiated network | `model/` | config hash + git SHA |
| 4. Training | dataset + model + training config | run directory (§3) | `training/` | `run_id` |
| 5. Evaluation / analysis | run directory + probe battery | `eval/`, `analysis/` outputs | `analysis/` | run_id + battery ID + analysis config hash |

Composed by Hydra; the composed config is validated by a pydantic model before
anything runs (both dependencies are already in `pixi.toml`). This catches config
typos at second zero instead of hour three.

### 2.1 Data generation / ingestion

- **Synthetic (first).** A RatInABox `Agent` produces the trajectory (position,
  velocity, head direction per bin). Its cell classes produce the input
  populations: `HeadDirectionCells` → "ADn", `PlaceCells` → "CA1", boundary-vector
  or egocentric/conjunctive cells → "RSC". Output is a zarr store with
  xarray-labeled dims `(time, channel)`, per-channel metadata (region, tuning
  parameters), and a `dataset.yaml` holding every generation parameter, the
  RatInABox version, the seed, the environment specification, and the content hash
  that becomes the `dataset_id`.
- **Open data.** DANDI dandiset ID + version + asset checksums; loaded via
  pynapple; preprocessing parameters (bin width, smoothing kernel, speed threshold)
  versioned in the same `dataset.yaml` shape.
- **Own recordings (later).** Same interface, same manifest shape.
- **Region tags on every input channel**, so "train without ADn" is a config flag,
  not a refactor.

### 2.2 Dataset assembly

- Window into sequences of length T with stride s (both in config).
- **Split by contiguous episodes / time blocks, never by random timesteps.**
  Trajectory autocorrelation means random-timestep splits leak the answer and make
  validation loss meaninglessly low. The split manifest (which episode IDs are in
  train/val/test) is saved with the dataset.
- **Hold out whole environments/routes** for the spatial-analogy tests: a held-out
  environment never appears in training in any form.
- Normalization statistics are computed on the training split only and stored.

### 2.3 Model

- **Core:** vanilla tanh RNN as the default — cleanest for fixed-point analysis and
  free of cuDNN fused-kernel nondeterminism. GRU (and possibly LSTM) as comparison
  arms.
- **Inputs:** per-region input projections, or one projection with region masks
  (either supports ablation; per-region projections make "which region drives which
  latent dimension" analyses easier).
- **Readouts:** linear. Position as (x, y). Head direction as (sin θ, cos θ) to
  avoid the wraparound discontinuity.
- **Horizon Δ** is a config parameter, never hardcoded to "next bin". A
  multi-horizon readout is a natural later extension.
- **Regularizers** (hidden-state noise injection, L2 on rates and/or weights) are
  first-class config entries. In the path-integration RNN literature these
  strongly shape *which* tuning emerges (Sorscher et al., 2023), so they must be
  logged and varied deliberately, never set once and forgotten.
- Architecture is fully specified by config; the code SHA is recorded alongside so
  the model can be rebuilt years later from `state_dict` + config.

### 2.4 Training

- Teacher-forced prediction of the target Δ bins ahead.
- Loss = w_pos · MSE(position) + w_hd · angular loss on head direction
  (1 − cos of the angular error, or a von Mises negative log-likelihood). **Both
  components are logged separately** — they converge at different rates.
- Optimizer and schedule from config. For science runs: cosine decay to zero over
  a fixed budget (§4), so "final checkpoint" is well-defined and comparable.
- Checkpoint cadence: log-spaced early (steps 0, 1, 2, 4, 8, …) then every N steps.
  Early representational change is fast; the log spacing is what makes emergence
  timelines legible.

### 2.5 Evaluation and analysis

- **Open-loop error** at horizon Δ (teacher-forced) — the standard metric, but a
  weak one (§4.1).
- **Multi-horizon evaluation** (predict 1, 5, 10, 20, … bins ahead with the
  open-loop model, or with a multi-horizon readout) — the primary discriminating
  task-side metric, available for every data kind.
- **Closed-loop rollouts** (feed predictions back in for k steps) are a
  path-integration stress test. Because the inputs are cell populations rather than
  raw position, closed-loop rollout requires *regenerating* input activity from the
  predicted state through the known synthetic tuning curves. This is possible for
  synthetic data only; treat it as a synthetic-only diagnostic and say so.
- **Probe battery and latent-space battery** (§5), run at every dumped checkpoint.

---

## 3. Run artifacts and reproducibility

### 3.1 Run directory layout

```
runs/2026-09-12_143201_a3f9c1/
├── manifest.yaml           # the one file that makes the run reconstructible (§3.2)
├── config.yaml             # fully-resolved Hydra config + the CLI overrides used
├── checkpoints/
│   ├── step_0000000.pt     # the init — saved, always; it is the null model
│   ├── step_0000001.pt     # log-spaced early, then every N steps
│   └── ...                 # each = weights + optimizer + scheduler + all RNG states
├── metrics.jsonl           # every logged scalar, locally; W&B mirrors this
├── probe_states/           # hidden-state dumps on the frozen probe battery
│   └── step_XXXXXXX.zarr   # dims (trial, time, unit), labeled via xarray, float16
├── eval/                   # open-loop, multi-horizon, rollout errors, predictions
└── analysis/               # outputs of the latent-space battery, per checkpoint
```

### 3.2 Manifest fields

Validated by a pydantic model; the same model is used to *load* runs for analysis,
so schema drift is caught rather than silently tolerated.

- **Identity:** `run_id`, creation time, full command line, parent run (if resumed
  or fine-tuned).
- **Code:** git SHA, dirty flag. Proposed policy: science runs refuse to start on a
  dirty tree (`allow_dirty: false` by default); debug runs may override and record
  a hash of the diff.
- **Environment:** hash of `pixi.lock`, pixi environment name (`default` / `cuda`),
  Python / PyTorch / CUDA / cuDNN versions, platform string.
- **Hardware:** hostname, CPU, GPU model, driver version.
- **Data:** `dataset_id`, dataset content hash, split-manifest hash, probe battery
  ID.
- **Config:** hash of the resolved config, plus the overrides.
- **Seeds:** `data_seed`, `init_seed`, `shuffle_seed` (and any augmentation seed).
- **Determinism:** the flags actually in effect (§3.4).
- **Status:** running / finished / aborted (with reason), step count, wall time.

### 3.3 Seed policy: three independent streams

Separate seeds for (a) data generation, (b) weight initialization, and (c)
dataloader shuffling / augmentation. Scientifically, "same dataset, 20 inits" and
"same init, 20 data draws" are *different experiments*, and a single global seed
entangles them. Each stream gets its own `torch.Generator` / NumPy `Generator`;
nothing draws from a global RNG inside the training loop.

### 3.4 Determinism settings

- `torch.use_deterministic_algorithms(True)`, `torch.backends.cudnn.deterministic =
  True`, `cudnn.benchmark = False`, `CUBLAS_WORKSPACE_CONFIG=:4096:8`.
- Dataloader workers seeded via `worker_init_fn` from the shuffle stream; shuffling
  uses an explicit generator.
- cuDNN's fused LSTM/GRU kernels are a classic nondeterminism source — one more
  reason the default core is a vanilla RNN.
- RatInABox leans on NumPy's global RNG: pin it explicitly in the data stage and
  record the RatInABox version in `dataset.yaml`.
- Record, do not hide, the limit: GPU kernels differ across hardware generations,
  so bitwise agreement is only expected within a (hardware, lock) pair. Across
  machines, the claim is replicability to a stated tolerance.

### 3.5 Data provenance

- `dataset_id` is a short content hash of the zarr store. Training verifies the
  on-disk hash against the manifest of the dataset it was pointed at and refuses to
  run on mismatch. This kills the "silently regenerated data" failure mode.
- Never regenerate in place: new parameters produce a new `dataset_id`. The
  `dataset.yaml` lives alongside the store and is committed to git (it is small);
  the store itself is not.

### 3.6 Storage habits

- **Save `state_dict` + config, never pickled modules.** A pickled module breaks the
  moment the class moves; a state dict plus the config that rebuilds the
  architecture is durable for years. Load with `weights_only=True`.
- **Local files are the record; W&B is a viewer.** `metrics.jsonl` and the run
  directory are the source of truth. If the W&B project evaporates, nothing is
  lost.
- **Do the arithmetic before inventing infrastructure.** For a ~512-unit RNN with
  ~300 input channels: ≈0.4 M parameters ≈ 1.7 MB in float32, ≈ 5 MB per checkpoint
  with Adam moments. 60 checkpoints × 20 seeds × 5 conditions ≈ 6,000 checkpoints
  ≈ 30 GB. That is "keep everything, forever" territory.
- **Hidden-state dumps are the only thing that grows fast.** A probe battery of 200
  trials × 500 bins × 512 units ≈ 51 M values ≈ 100 MB per checkpoint in float16.
  Dump at ~15 log-spaced checkpoints → ~1.5 GB per run; 100 runs → ~150 GB. So:
  float16, log-spaced checkpoints only, and possibly only for seeds designated for
  developmental analysis.
- **Where it lives:** git holds manifests, configs, `dataset.yaml`, and split
  manifests. Weights, stores, and dumps live in content-addressed run directories
  synced to external storage — DVC if a managed remote is wanted; at these sizes
  even git-lfs would work for checkpoints.

### 3.7 Multi-seed protocol

- Pilot: 5 init seeds per condition. Science: ≥ 10 (20 if the geometry claims
  turn out to be subtle).
- **Identical step budgets across all seeds and conditions in any comparison**
  (§4.2). This is what makes cross-seed geometry differences attributable to seeds
  rather than to training duration.
- Report distributions, not the best seed. Hierarchical estimates (seed within
  condition) via the PyMC / ArviZ stack already in the environment.

---

## 4. Stopping criterion

### 4.1 Why validation-loss early stopping is the wrong primary rule

- **One-step teacher-forced loss is a weak, fast-saturating signal.** Rat
  trajectories are smooth, so "position(t+1) ≈ position(t) + a bit of velocity"
  gets most of the way; the loss largely measures smoothness and plateaus early
  with poor resolution. Multi-horizon error (and, on synthetic data, closed-loop
  rollout error) is far more discriminating.
- **The loss is not the object of study; the representation is.** Across the
  path-integration-RNN literature (Cueva & Wei, 2018; Banino et al., 2018; Sorscher
  et al., 2023) and the grokking literature generally (Power et al., 2022),
  representational geometry keeps reorganizing well after task loss flattens —
  structure often emerges *during* the plateau. Early stopping at the plateau
  systematically truncates the phase that matters. Conversely, very long
  overtraining can simplify or collapse representations. The plateau marks where to
  start paying attention, not where to stop.
- **Run-dependent stopping times confound comparisons.** If seed A stops at 10 k
  steps and seed B at 60 k, any cross-seed geometry difference is confounded with
  training duration, and the replicability claim evaporates.

### 4.2 The rule: fixed budget, identical across runs

1. **Pilot.** 3–5 seeds per condition, generous budget (e.g. 200 k steps).
   Define the plateau step as the first step after which relative improvement in
   validation multi-horizon error over a window W stays below ε (W and ε recorded
   in the analysis config).
2. **Budget.** Science budget = c × plateau step with c ≈ 3, rounded up, frozen
   in the training config, and the same for every seed and condition in a
   comparison. Cosine learning-rate decay to zero over the budget. Avoid
   reduce-on-plateau schedules: they couple the schedule to a noisy signal and make
   runs non-comparable.
3. **Guards, for genuine failure only.** NaN/inf in loss or weights → abort.
   Gradient-norm explosion beyond a logged threshold → abort. Validation error not
   beating a trivial baseline (constant-velocity extrapolation) by a warmup step →
   abort as a failed run. Aborted runs are kept with `status: aborted`, never
   deleted — they are data about the training landscape.

### 4.3 Checkpoint selection, pre-registered

The rule is written in the analysis config *before* looking at any latent-space
result. Candidate rules, in order of simplicity:

1. **Final checkpoint.** With cosine-to-zero it is well-defined and needs no
   judgment. Default.
2. **First checkpoint after plateau.** Useful for asking what the representation
   looks like at the point the task is "solved".
3. **Best validation multi-horizon error.**

Primary analyses are reported at *early / plateau / final* checkpoints so
robustness to the choice is visible rather than asserted.

### 4.4 Convergence certificate

Reported per run at the end of training:

- **Task-side:** slope of validation multi-horizon error over the last 20 % of
  training ≈ 0 within noise.
- **Representation-side:** linear CKA (Kornblith et al., 2019) between probe-set
  hidden states at consecutive dumped checkpoints ≥ threshold (e.g. 0.98) over the
  last 20 % of training — i.e. the geometry itself has stopped moving. This is the
  principled answer to "has the latent space converged", and it is
  *property-neutral*.

If either criterion fails, the run is flagged *unsettled*. The remedy is to extend
the budget **for the whole condition** and re-run, not to extend that one run — so
identical budgets are preserved.

### 4.5 The inviolable rule

> **Never use axis-of-travel or spatial-analogy metrics as a stopping or selection
> criterion.** If training stops, or a checkpoint is chosen, when axis tuning
> looks strongest, "axis coding emerges in the trained network" stops being a
> finding and becomes an artifact of the procedure. Compute these metrics at every
> dumped checkpoint, log them, plot their emergence timelines — *monitor, never
> optimize or select on them.* Selection uses only task-side signals (§4.3) or
> property-neutral convergence (§4.4). The emergence timeline relative to the loss
> plateau is then itself a result, not a contamination.

### 4.6 What gets logged during training

| Kind | Signal | Used for stopping / selection? |
|---|---|---|
| Task-side | train/val loss, per component (position, HD) | no (guards only) |
| Task-side | validation multi-horizon error | plateau detection, selection rule 3 |
| Task-side | closed-loop rollout error (synthetic only) | no; diagnostic |
| Task-side | constant-velocity baseline comparison | failed-run guard |
| Optimization | gradient norm, weight norms, learning rate | divergence guard |
| Representation | participation ratio / PCA spectrum of probe states | no |
| Representation | CKA to previous checkpoint and to final | convergence certificate only |
| Representation | axis-tuning index distribution; decoding of axis / HD / position | **never** |

---

## 5. Latent-space readiness

### 5.1 Frozen probe battery

A versioned dataset with its own ID, run through the network at every dumped
checkpoint for every seed. Designed to *dissociate* variables that natural foraging
entangles (RatInABox supports imposed trajectories via `Agent.import_trajectory`):

- **A — same location, different axes.** Crossings of the same point along four or
  more axes.
- **B — same axis, different locations.** Parallel straight runs across the arena.
- **C — both directions along each axis.** Without this, axis tuning cannot be
  distinguished from ordinary direction tuning.
- **D — natural foraging segments** (held-out) for ecological validity.
- **E — spatial-analogy set.** Geometrically similar routes at different locations
  and orientations, plus held-out environments.

Each probe trial carries coordinates for position, head direction, travel axis
(direction mod 180°), speed, environment, and trial type, so every analysis can
condition on them directly from the labeled array.

### 5.2 Checkpoint 0 as the null model

Random RNNs already show nontrivial tuning. Every emergence claim is "relative to
init", so the initial weights are a control condition, not optional metadata.
Shuffle controls (permuted labels, time-shifted labels) complement it.

### 5.3 Hidden-state dumps

xarray with dims `(trial, time, unit)` and the coordinates above, stored per
dumped checkpoint in zarr as float16. This is the single most valuable artifact
for post-training analysis: "watch the axis subspace emerge over training" becomes
an offline notebook analysis rather than a retrain.

### 5.4 Analysis battery

- **Unit-level axis tuning.** Regress each unit's activity on
  (cos θ, sin θ, cos 2θ, sin 2θ) plus position covariates. Axis tuning is
  direction modulo 180°, i.e. power at the double angle; an axis index compares
  the 2θ and θ terms. Align the criteria with those used for real subiculum data
  (Olson et al., 2017) so model and animal are scored the same way.
- **Population-level.** Cross-validated linear decoders for axis, head direction,
  and position (decoded on held-out probe trials); demixed PCA (Kobak et al., 2016)
  or targeted dimensionality reduction to isolate an axis subspace; participation
  ratio (Gao et al., 2017) over training.
- **Dynamics.** Fixed-/slow-point analysis (Sussillo & Barak, 2013; Golub &
  Sussillo, 2018). A ring of slow points would suggest inherited head-direction
  attractor structure; discrete or line-attractor structure organized by axis
  would be the more interesting outcome.
- **Cross-seed geometry.** CKA and Procrustes shape metrics (Williams et al., 2021)
  between seeds, and dynamics-level comparison (Maheswaranathan et al., 2019).
  Units will not replicate across seeds; if the geometry does, that is a
  representation-level replicability claim in the README's sense — valid only
  under identical budgets (§3.7, §4.2).
- **Developmental.** All of the above as a function of checkpoint, producing
  emergence timelines aligned to the plateau step.

### 5.5 Controls and ablations

Untrained network; shuffled labels; input ablations (train without ADn / CA1 /
RSC); horizon Δ sweep; regularizer sweep (noise, L2) since these are known to
shape emergent tuning; cell-type comparison (tanh RNN vs GRU).

---

## 6. Open decisions before implementation

| Decision | Proposed default | Notes |
|---|---|---|
| Recurrent cell | tanh RNN; GRU as comparison arm | analysis-friendly, deterministic on GPU |
| Time bin and horizon Δ | bin 20–50 ms; Δ swept over several bins | RatInABox default `dt` is finer; downsample explicitly |
| Input population sizes per region | to be set from pilot; record in `dataset.yaml` | keep ratios plausible, not necessarily biological counts |
| Probe battery composition | sets A–E above | freeze before science runs |
| Budget calibration | 5-seed pilot, c = 3 × plateau step | record ε, W, and the plateau step per condition |
| Seeds per condition | 5 pilot, ≥ 10 science | |
| Hidden-state dumps | float16, log-spaced checkpoints, designated seeds | budget per §3.6 |
| Storage sync target | DVC remote vs external drive vs git-lfs | decide once run sizes are real |
| Dirty-tree policy | science runs refuse to start on a dirty tree | debug runs may override |
| Closed-loop rollouts | synthetic only, via regenerated inputs | state the limitation in figures |
| Checkpoint selection rule | final checkpoint (rule 1) | pre-register in analysis config |

---

## 7. References (starting points)

- Olson JM, Tongprasearth K, Nitz DA (2017). Subiculum neurons map the current
  axis of travel. *Nature Neuroscience* 20:170–172.
- Cueva CJ, Wei X-X (2018). Emergence of grid-like representations by training
  recurrent neural networks to perform spatial localization. *ICLR*.
- Banino A et al. (2018). Vector-based navigation using grid-like representations
  in artificial agents. *Nature* 557:429–433.
- Sorscher B, Mel GC, Ocko SA, Giocomo LM, Ganguli S (2023). A unified theory for
  the computational and mechanistic origins of grid cells. *Neuron* 111.
- Sussillo D, Barak O (2013). Opening the black box: low-dimensional dynamics in
  high-dimensional recurrent neural networks. *Neural Computation* 25:626–649.
- Golub MD, Sussillo D (2018). FixedPointFinder: a TensorFlow toolbox for
  identifying and characterizing fixed points in recurrent neural networks.
  *JOSS* 3(31):1003.
- Maheswaranathan N, Williams AH, Golub MD, Ganguli S, Sussillo D (2019).
  Universality and individuality in neural dynamics across large populations of
  recurrent networks. *NeurIPS*.
- Kornblith S, Norouzi M, Lee H, Hinton G (2019). Similarity of neural network
  representations revisited. *ICML*.
- Williams AH, Kunz E, Kornblith S, Linderman SW (2021). Generalized shape metrics
  on neural representations. *NeurIPS*.
- Kobak D et al. (2016). Demixed principal component analysis of neural population
  data. *eLife* 5:e10989.
- Gao P et al. (2017). A theory of multineuronal dimensionality, dynamics and
  measurement. *bioRxiv*.
- Power A, Burda Y, Edwards H, Babuschkin I, Misra V (2022). Grokking:
  generalization beyond overfitting on small algorithmic datasets.
  *arXiv:2201.02177*.
- George TM et al. (2024). RatInABox, a toolkit for modelling locomotion and
  neuronal activity in continuous environments. *eLife* 13:e85274.
- Peyrache A, Lacroix MM, Petersen PC, Buzsáki G (2015). Internally organized
  mechanisms of the head direction sense. *Nature Neuroscience* 18:569–575.
  (ADn recordings; candidate open dataset.)
- PyTorch reproducibility notes:
  https://pytorch.org/docs/stable/notes/randomness.html
- National Academies of Sciences, Engineering, and Medicine (2019).
  *Reproducibility and Replicability in Science.* https://doi.org/10.17226/25303
