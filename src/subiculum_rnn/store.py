"""
The artifact store: how it is found, its marker, its layout and the artifacts inside it.
"""

import os
import socket
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from . import __version__
from .paths import repo_root

ENV_VAR = "SUBICULUM_RNN_STORE"
MARKER = "store.yaml"
MANIFEST = "manifest.yaml"
STORE_VERSION = 1
KINDS = ("datasets", "models", "experiments")


class StoreError(Exception):
    pass


@dataclass(frozen=True)
class Artifact:
    id: str
    path: Path
    meta: dict


def _scan(directory: Path) -> tuple[list[Artifact], list[str], list[str]]:
    """
    Artifacts by id, directories without a manifest, and manifests with the wrong id.
    """
    if not directory.is_dir():
        return [], [], []
    artifacts, unmarked, broken = [], [], []
    for d in sorted(p for p in directory.iterdir() if p.is_dir()):
        manifest = d / MANIFEST
        if not manifest.is_file():
            unmarked.append(f"{d.name} has no {MANIFEST}")
            continue
        meta = yaml.safe_load(manifest.read_text())
        if not isinstance(meta, dict):
            broken.append(f"{d.name}/{MANIFEST} is not a mapping")
        elif meta.get("id", d.name) != d.name:
            broken.append(f"{d.name}/{MANIFEST} declares id {meta['id']!r}")
        else:
            artifacts.append(Artifact(id=d.name, path=d, meta=meta))
    return artifacts, unmarked, broken


def git_commit() -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root(),
                             capture_output=True, text=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip()


@dataclass(frozen=True)
class Store:
    root: Path
    source: str  # flag, env, default, argument

    @property
    def marker(self) -> Path:
        return self.root / MARKER

    @property
    def initialized(self) -> bool:
        return self.marker.is_file()

    def kind_dir(self, kind: str) -> Path:
        return self.root / kind

    def read_marker(self) -> dict:
        if not self.initialized:
            raise StoreError(f"store not found at {self.root}; "
                             f"is the drive mounted? run `store init`")
        marker = yaml.safe_load(self.marker.read_text()) or {}
        version = marker.get("store_version")
        if not isinstance(version, int) or version > STORE_VERSION:
            raise StoreError(f"store at {self.root} has store_version {version!r}; "
                             f"this tool supports {STORE_VERSION}, update the tool")
        return marker

    def init(self) -> dict:
        if self.initialized:
            return self.read_marker()
        for kind in KINDS:
            self.kind_dir(kind).mkdir(parents=True, exist_ok=True)
        marker = {
            "store_version": STORE_VERSION,
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "hostname": socket.gethostname(),
            "repo_commit": git_commit(),
            "tool_version": __version__,
        }
        self.marker.write_text(yaml.safe_dump(marker, sort_keys=False))
        return marker

    def artifacts(self, kind: str) -> list[Artifact]:
        artifacts, _, broken = _scan(self.kind_dir(kind))
        if broken:
            raise StoreError(f"{self.kind_dir(kind)}: " + "; ".join(broken))
        return artifacts

    def survey(self) -> tuple[dict[str, int], list[str]]:
        counts, problems = {}, []
        for kind in KINDS:
            artifacts, unmarked, broken = _scan(self.kind_dir(kind))
            counts[kind] = len(artifacts)
            problems += [f"{kind}/{p}" for p in unmarked + broken]
        return counts, problems


def resolve_store(flag: str | None, env: Mapping[str, str] | None = None) -> Store:
    env = os.environ if env is None else env
    if flag:
        return Store(Path(flag).expanduser(), "flag")
    if env.get(ENV_VAR):
        return Store(Path(env[ENV_VAR]).expanduser(), "env")
    return Store(repo_root() / "artifacts", "default")


def open_store(flag: str | None, env: Mapping[str, str] | None = None) -> Store:
    store = resolve_store(flag, env)
    store.read_marker()
    return store
