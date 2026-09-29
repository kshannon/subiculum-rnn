from pathlib import Path


def repo_root() -> Path:
    """The checkout containing this package (src/subiculum_rnn/paths.py)."""
    return Path(__file__).resolve().parents[2]


def configs_dir() -> Path:
    return repo_root() / "configs"


def environments_dir() -> Path:
    return configs_dir() / "environments"
