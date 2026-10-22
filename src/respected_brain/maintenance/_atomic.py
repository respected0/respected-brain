"""Atomic final note replacement, including DataRoot staging on another volume."""
from __future__ import annotations

import errno
import os
from pathlib import Path
import shutil
import tempfile


def replace_staged(staging: Path, destination: Path) -> None:
    try:
        os.replace(staging, destination)
        return
    except OSError as error:
        if error.errno != errno.EXDEV and getattr(error, "winerror", None) != 17:
            raise
    # A same-volume commit file is required for atomic replacement. Only this
    # short-lived final commit lives beside the note; durable staging is DataRoot.
    descriptor, name = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    commit = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as output:
            with staging.open("rb") as source:
                shutil.copyfileobj(source, output)
            output.flush()
            os.fsync(output.fileno())
        os.replace(commit, destination)
        staging.unlink(missing_ok=True)
    finally:
        commit.unlink(missing_ok=True)


def write_text_staged(path: Path, content: str, *, temp_dir: Path | None = None) -> None:
    """Write text atomically via temporary file and atomic rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if temp_dir is not None:
        temp_dir.mkdir(parents=True, exist_ok=True)
    safe_prefix = "".join(c if c.isalnum() or c in ("-", "_", ".") else "_" for c in path.name)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{safe_prefix}.", dir=temp_dir or path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        replace_staged(temporary, path)
    except BaseException:
        try:
            os.close(descriptor)
        except OSError:
            pass
        temporary.unlink(missing_ok=True)
        raise
