"""The artifact store: where datasets, models and experiments live.

A store is a directory outside git, on this machine or an external drive,
holding a ``store.yaml`` marker and one directory per artifact kind. It is
chosen per invocation by ``--store``, per machine by the SUBICULUM_RNN_STORE
environment variable, and otherwise defaults to ``artifacts/`` inside the
checkout. Commands only touch a marked store, which catches an unmounted
drive or a mistyped path before anything is written. Nothing else lives in
a store.
"""

import os
import socket
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

import yaml

from . import __version__
from .experiments.registry import scan_manifests
from .paths import repo_root

ENV_VAR = "SUBICULUM_RNN_STORE"
MARKER = "store.yaml"
STORE_VERSION = 1
KINDS = ("datasets", "models", "experiments")


class StoreError(Exception):
    """The store cannot be used; the message says why and what to do."""


def default_store_root() -> Path:
    return repo_root() / "artifacts"


def git_commit() -> str | None:
    """HEAD of the checkout containing the package, or None outside git."""
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root(),
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


@dataclass(frozen=True)
class Store:
    root: Path
    source: str          # how it was chosen: flag, env, default, argument

    @property
    def marker(self) -> Path:
        return self.root / MARKER

    @property
    def initialized(self) -> bool:
        return self.marker.is_file()

    def kind_dir(self, kind: str) -> Path:
        if kind not in KINDS:
            raise ValueError(f"unknown artifact kind {kind!r}; known: {KINDS}")
        return self.root / kind

    def read_marker(self) -> dict:
        """The marker's contents. Raises StoreError if the store is unusable."""
        if not self.root.is_dir():
            raise StoreError(f"store not found at {self.root}; is the drive "
                             f"mounted? run `store init`")
        if not self.marker.is_file():
            raise StoreError(f"{self.root} is not a store (no {MARKER}); "
                             f"run `store init`")
        marker = yaml.safe_load(self.marker.read_text()) or {}
        version = marker.get("store_version")
        if not isinstance(version, int) or version > STORE_VERSION:
            raise StoreError(f"store at {self.root} has version {version}; "
                             f"this tool supports {STORE_VERSION}, update the tool")
        return marker

    def init(self) -> dict:
        """Create the layout and marker. An initialized store is left as is."""
        if self.initialized:
            return self.read_marker()
        self.root.mkdir(parents=True, exist_ok=True)
        for kind in KINDS:
            self.kind_dir(kind).mkdir(exist_ok=True)
        marker = {
            "store_version": STORE_VERSION,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "hostname": socket.gethostname(),
            "repo_commit": git_commit(),
            "tool_version": __version__,
        }
        self.marker.write_text(yaml.safe_dump(marker, sort_keys=False))
        return marker

    def check(self) -> list[str]:
        """Problems found: missing kind directories, subdirectories without a
        manifest, manifests whose id differs from their directory."""
        problems = []
        for kind in KINDS:
            directory = self.kind_dir(kind)
            if not directory.is_dir():
                problems.append(f"{kind}/ is missing")
                continue
            problems += [f"{kind}/{p}" for p in scan_manifests(directory)[1]]
        return problems

    def counts(self) -> dict[str, int]:
        """Valid artifacts per kind."""
        return {kind: len(scan_manifests(self.kind_dir(kind))[0]) for kind in KINDS}


def resolve_store(flag: str | None, env: Mapping[str, str] | None = None) -> Store:
    """Pick the store without checking it: flag, then environment, then default."""
    env = os.environ if env is None else env
    if flag:
        return Store(Path(flag).expanduser(), "flag")
    if env.get(ENV_VAR):
        return Store(Path(env[ENV_VAR]).expanduser(), "env")
    return Store(default_store_root(), "default")


def open_store(flag: str | None, env: Mapping[str, str] | None = None) -> Store:
    """Resolve the store and require its marker."""
    store = resolve_store(flag, env)
    store.read_marker()
    return store
