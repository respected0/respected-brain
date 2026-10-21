"""Locating the transcript file of a known Codex or Antigravity session without scanning user data."""
from __future__ import annotations
import os
from pathlib import Path
import re
from respectedbrain.core.platform import path_within_vault

SESSION_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")


def resolve_antigravity_transcript(
    session_id: str,
    home: Path | None = None,
) -> str:
    """Resolve a known Antigravity transcript without scanning user data."""

    if (
        SESSION_COMPONENT.fullmatch(session_id) is None
        or session_id in {".", ".."}
    ):
        return ""
    profile = home or Path.home()
    for product in ("antigravity-ide", "antigravity-cli", "antigravity"):
        brain = profile / ".gemini" / product / "brain"
        candidate = (
            brain
            / session_id
            / ".system_generated"
            / "logs"
            / "transcript.jsonl"
        )
        try:
            candidate.resolve(strict=True).relative_to(brain.resolve(strict=True))
        except (OSError, RuntimeError, ValueError):
            continue
        if candidate.is_file():
            return str(candidate)
    return ""


def resolve_codex_transcript(
    session_id: str,
    home: Path | None = None,
) -> str:
    """Resolve a known Codex rollout transcript without scanning entire user data."""

    if (
        SESSION_COMPONENT.fullmatch(session_id) is None
        or session_id in {".", ".."}
        or session_id.endswith("-unknown")
    ):
        return ""
    profile = home or Path.home()
    codex_home = profile / ".codex"
    if not codex_home.is_dir():
        return ""
    for folder_name in ("sessions", "archived_sessions"):
        root = codex_home / folder_name
        if not root.is_dir() or not path_within_vault(root, codex_home):
            continue
        matches = []
        for directory, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if path_within_vault(Path(directory) / d, codex_home)]
            for filename in files:
                if not (filename == session_id + '.jsonl' or filename.endswith('-' + session_id + '.jsonl')):
                    continue
                match = Path(directory) / filename
                try:
                    if path_within_vault(match, codex_home) and match.is_file():
                        matches.append((match.stat().st_mtime, str(match)))
                except (OSError, RuntimeError, ValueError):
                    continue
        if matches:
            return max(matches)[1]
    return ""
