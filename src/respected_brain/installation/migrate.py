"""Move the person's data files to this build's format in place, before anything reads them.

A new build that changes a file's `schema_version` adds one step per old version to STEPS; `repair` and `setup` run
this first, so an update never asks the person for anything. The original is kept next to the file as `<name>.v<N>.bak`.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from respected_brain.core.config import atomic_write_bytes
from respected_brain.core.errors import FoundationError

# file name in the data root -> current schema_version
CURRENT = {"config.json": 3, "install-manifest.json": 3, "memory-grants.json": 1}
# the oldest version a release shipped (0.1.0-beta.1); every version from there to CURRENT needs a step
SHIPPED = {"config.json": 3, "install-manifest.json": 3, "memory-grants.json": 1}
# (file name, from_version) -> function turning that version's document into the next version's
STEPS: dict[tuple[str, int], Callable[[dict], dict]] = {}


def migrate_data(data_root: Path, *, current=CURRENT, steps=STEPS) -> list[str]:
    """Returns the names of the files that were moved; unknown (newer) or damaged data is reported, never overwritten."""
    moved = []
    for name, target in current.items():
        path = Path(data_root) / name
        if not path.is_file():
            continue
        original = path.read_bytes()
        try:
            document = json.loads(original)
        except ValueError as error:
            raise FoundationError(f"{name} okunamadı; dosyayı düzeltin ya da yedeğe alıp silin") from error
        version = document.get("schema_version") if isinstance(document, dict) else None
        if not isinstance(version, int) or isinstance(version, bool):
            raise FoundationError(f"{name} biçimi tanınmıyor (schema_version yok)")
        if version > target:
            raise FoundationError(f"{name} daha yeni bir sürümden (biçim {version}); programı güncelleyin")
        if version == target:
            continue
        for step in range(version, target):
            if (name, step) not in steps:
                raise FoundationError(f"{name} için biçim {step} → {step + 1} taşıması yok")
            document = steps[(name, step)](document)
            document["schema_version"] = step + 1
        backup = path.with_name(f"{name}.v{version}.bak")
        if not backup.exists():
            atomic_write_bytes(backup, original)
        atomic_write_bytes(path, (json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8"))
        moved.append(name)
    return moved
