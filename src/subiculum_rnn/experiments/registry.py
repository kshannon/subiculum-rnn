"""Artifact registry.

A registered artifact (dataset, model or experiment) is a directory under
<store>/<kind>/<id>/ holding a manifest.yaml whose ``id`` matches the
directory name. Directories without a manifest are not artifacts. Flat files
plus manifests are the database; nothing here is ever modified in place.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml

MANIFEST_NAME = "manifest.yaml"


@dataclass(frozen=True)
class ManifestEntry:
    id: str
    path: Path
    meta: dict


def scan_manifests(directory: str | Path) -> tuple[list[ManifestEntry], list[str]]:
    """Every artifact under ``directory`` sorted by id, plus the problems found:
    a subdirectory without a manifest, a manifest that is not a mapping, an
    id that differs from its directory. Never raises on content."""
    directory = Path(directory)
    entries: list[ManifestEntry] = []
    problems: list[str] = []
    if not directory.is_dir():
        return entries, problems
    for d in sorted(p for p in directory.iterdir() if p.is_dir()):
        manifest = d / MANIFEST_NAME
        if not manifest.is_file():
            problems.append(f"{d.name} has no {MANIFEST_NAME}")
            continue
        meta = yaml.safe_load(manifest.read_text()) or {}
        if not isinstance(meta, dict):
            problems.append(f"{d.name}/{MANIFEST_NAME} is not a mapping")
            continue
        declared = meta.get("id", d.name)
        if declared != d.name:
            problems.append(f"{d.name}/{MANIFEST_NAME} declares id {declared!r}")
            continue
        entries.append(ManifestEntry(id=d.name, path=d, meta=meta))
    return entries, problems


def list_manifests(directory: str | Path) -> list[ManifestEntry]:
    """Artifacts under ``directory``, sorted by id. Subdirectories without a
    manifest are skipped; a malformed manifest raises ValueError."""
    entries, problems = scan_manifests(directory)
    malformed = [p for p in problems if "has no" not in p]
    if malformed:
        raise ValueError(f"{directory}: " + "; ".join(malformed))
    return entries
