# subiculum-rnn

A recurrent neural network trained to predict future position and head direction from inputs to subiculum (e.g. ADn, CA1, RSC). The latent space is examined for emergent axis-of-travel and spatial-analogy representations.

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


Synthetic, and open source data results should be reproducible. Results using your own collected recording data should be replicable to within some stated percision. Given the stochastic nature of machine learning methods, from data cleaning to pipeline construction to training and validation, it can be daunting to provide 100% reproducibility, but it is a standard to strive for nonetheless. 

To that end, this README provides all instructions needed to reproduce our synthetic data results. Instructions for reproducing results with open-source data and our own recorded data are provided in the project wiki.


| Requirement | How it's met |
|-------------|-------------|
| **Exact software versions** | `pixi.lock` pins every Python package, and its transitive dependencies, to a specific version |
| **Versioned data provenance** | Each synthetic dataset has a config.yaml with all generation parameters + an ID |
| **Logged and versioned training runs** | Hydra configs are saved with each run and WandB logs every metric |
| **Cross-platform** | `pixi.toml` targets `linux-64`, `osx-arm64` |


## Citation

If you use this code, please cite the relevant papers (see project wiki for full reference list of papers and open source citable libraries).

**Cite this project**: `¯\_(ツ)_/¯` One Day!

---

1. National Academies of Sciences, Engineering, and Medicine. 2019. Reproducibility and Replicability in Science. Washington, DC: The National Academies Press. https://doi.org/10.17226/25303.
2. https://www.acm.org/publications/policies/artifact-review-and-badging-current
