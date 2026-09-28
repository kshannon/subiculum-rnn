"""Configs always come from the checkout containing the package."""

from subiculum_rnn.paths import environments_dir, repo_root


def test_configs_resolve_inside_the_checkout():
    assert (repo_root() / "pyproject.toml").exists()
    assert environments_dir() == repo_root() / "configs" / "environments"
