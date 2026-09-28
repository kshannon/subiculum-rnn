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

# 3. Install environment and dependencies
pixi install
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
| **Versioned data provenance** | Each synthetic dataset has a config.yaml with all generation parameters + an ID |
| **Logged and versioned training runs** | Hydra configs are saved with each run and WandB logs every metric |
| **Cross-platform** | `pixi.toml` targets `linux-64`, `osx-arm64` |

## Pixi task command samples
`pixi run env-plot triple_t --out figures/env.png && open figures/env.png`


## Citation

If you use this code, please cite the relevant papers (see project wiki for full reference list of papers and open source citable libraries).

**Cite this project**: `¯\_(ツ)_/¯` One Day!

---

1. National Academies of Sciences, Engineering, and Medicine. 2019. Reproducibility and Replicability in Science. Washington, DC: The National Academies Press. https://doi.org/10.17226/25303.
2. https://www.acm.org/publications/policies/artifact-review-and-badging-current
3. Tom M George, Mehul Rastogi, William de Cothi, Claudia Clopath, Kimberly Stachenfeld, Caswell Barry. "RatInABox, a toolkit for modelling locomotion and neuronal activity in continuous environments" (2024), eLife, https://doi.org/10.7554/eLife.85274 .
