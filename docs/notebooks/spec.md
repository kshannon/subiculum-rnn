# Notebook template

PR on branch `agents/notebook-template`: one command that creates a Jupyter notebook in
`notebooks/` from a standard template, so a new notebook never starts by copy-pasting.

## Overview

`subiculum-rnn notebook new <name>` copies `templates/notebook.ipynb` to
`notebooks/YYYY-MM-DD_<name>.ipynb`, filling in the title, date and name. The template is
a real notebook, edited in Jupyter like any other, so changing what every new notebook
starts with means editing one file, not code. A notebook is a working document, not an
artifact: nothing here touches the store or manifests.

## Functional Requirements

### Command

- `subiculum-rnn notebook new <name> [--title TEXT] [--dir DIR]`: create the notebook and
  print its path. `<name>` is slugified the way `pixi run note` slugifies lab notebook
  names (lowercase, runs of non-alphanumerics become one dash). `--title` defaults to the
  name with dashes turned into spaces. `--dir` defaults to `notebooks/` in the checkout.
- `pixi run notebook <name>` is the same command as a pixi task.
- Refuses to overwrite: an existing file at the target path is an error naming it, exit 2.
  An empty slug is an error, exit 2.
- The `notebook` group joins the CLI spec's command table; it is the first group whose
  only command is real.

### Template contents, in cell order

1. Markdown header: `# <date> <title>`, then name, created timestamp, and a Purpose line
   to fill in; a one-line reminder of non-negotiable 1 (nothing that encodes axis of
   travel reaches training inputs) with a link to AGENTS.md; a link to the relevant spec.
2. Code, setup: `%load_ext autoreload`, `%autoreload 2`, `%matplotlib inline`,
   `%config InlineBackend.figure_format = "retina"`; imports: `Path`, `numpy as np`,
   `pandas as pd`, `matplotlib.pyplot as plt`, `scienceplots` (registers the styles),
   `subiculum_rnn`, `load_environment` and `list_environments` from the environments
   package, `resolve_store` from the store; `plt.style.use(["science", "notebook",
   "no-latex"])`; `rng = np.random.default_rng(0)`; `store = resolve_store(None)`; a
   context print of package version, git commit, store path and today's date.
3. Code, sample figure in the SciencePlots style: two panels, the triple-T walls drawn
   from `load_environment("triple_t")` with equal aspect, and a line plot with a legend;
   a `FIGURES = Path("figures")` and a commented `fig.savefig(FIGURES / ..., dpi=300)`.
4. Markdown section headers with a one-line hint each: Data, Analysis, Figures, Notes.

Placeholders in the template are `{{DATE}}`, `{{TITLE}}`, `{{NAME}}`, `{{CREATED}}`,
replaced in every cell's source. Everything else is copied verbatim, outputs included,
so the template ships with the sample figure already rendered.

### Behavior

- Generated notebooks are committed like any other file; clear outputs before committing
  large ones. Exploratory notebooks are disposable; report notebooks cite artifact ids.
- LaTeX is not required: `no-latex` is in the default style list. Remove it in a notebook
  when a TeX installation is present and publication typography is wanted.

## Non-Functional Requirements

- `src/subiculum_rnn/notebooks.py` holds one function, `new_notebook(name, title, directory,
  today)`, reading and writing through `nbformat`; `cli/notebook.py` is the group module.
- Dependencies, dev feature only: `nbformat` (already present through jupyter, declared
  explicitly) and `scienceplots` from PyPI. `nbformat` is imported inside the function so
  the CLI's import cost does not change.
- SciencePlots is credited in the README references with its Zenodo citation
  (John D. Garrett, garrettj403/SciencePlots, doi 10.5281/zenodo.4106649) and in the PR.
- One test: the generated file validates with `nbformat`, its first cell contains the date
  and title, and a second call with the same name exits 2. Strike it if not wanted.

## Out of Scope

- Executing notebooks, converting them to reports, or parameterizing them (papermill).
- Stripping outputs on commit (nbstripout); revisit when notebooks accumulate.
- Subfolders under `notebooks/`; `--dir` covers other locations.
- Registering notebooks in the store or linking them to artifacts.
- A LaTeX installation or the `ieee` and `nature` styles.
