"""RPP `memory.semantic.status|configure|pull`: opt-in local semantic search (FTS keeps working without it)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .integrations import _context
from .memory import MemoryOpError, _active_vault_id, _bad
from ..search import semantic
from ..search.engine import IndexUnavailable, SearchEngine

_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,79}$")


def _wrap(call):
    try:
        return call()
    except semantic.SemanticError as error:
        raise MemoryOpError(error.code, error.message, error.hint) from None


def status(data_root: Path) -> dict[str, Any]:
    """Read-only: configuration, local service/model availability and vector coverage."""
    data_root = Path(data_root)
    if not _active_vault_id(data_root):
        raise MemoryOpError("NO_VAULT", "No vault is registered.", "Register a vault in the Brain product first.")
    cfg = semantic.load_config(data_root)
    provider = semantic.provider_state(data_root, cfg)
    _, ctx = _context(data_root, {})
    try:
        with SearchEngine.open_read_only(ctx)._get_connection() as con:
            notes = con.execute("SELECT COUNT(*) FROM files_meta").fetchone()[0]
    except (IndexUnavailable, ValueError):
        notes = 0
    vectors = semantic.vector_count(ctx, cfg["model"])
    if not cfg["enabled"]:
        state = "off"
    elif provider["provider"] != "up" and cfg["provider"] == "ollama":
        state = "provider_missing"
    elif provider["provider"] != "up" or not provider["model_installed"]:
        state = "model_missing"
    else:
        state = "ready" if notes and vectors >= notes else "building"
    return {"state": state, "enabled": cfg["enabled"], "model": cfg["model"], "provider": cfg["provider"], "service": provider["provider"],
            "download_mb": semantic.DOWNLOAD_MB if cfg["provider"] == "llama" else None,
            "model_installed": provider["model_installed"] and provider["provider"] == "up", "notes": notes, "vectors": vectors, "local_only": True}


def configure(data_root: Path, payload: Any) -> dict[str, Any]:
    """Turn semantic search on/off (and pick the model). Writes only `semantic.json` in the data root."""
    if (not isinstance(payload, dict) or set(payload) - {"confirm", "enabled", "model", "provider"} or payload.get("confirm") is not True
            or not isinstance(payload.get("enabled"), bool)):
        raise _bad("Invalid payload.", "Send {confirm: true, enabled: bool, model?: str}.")
    cfg = semantic.load_config(data_root)
    provider = payload.get("provider", cfg["provider"])
    if provider not in semantic.PROVIDERS:
        raise _bad("Invalid provider.", "Use llama (managed by the Hub) or ollama.")
    model = payload.get("model", cfg["model"] if provider == cfg["provider"] else ("bge-m3-Q4_K_M" if provider == "llama" else "nomic-embed-text"))
    if not isinstance(model, str) or not _MODEL_RE.match(model) or (provider == "llama" and model not in semantic.MODELS):
        raise _bad("Invalid model name.", "Known models: " + ", ".join(semantic.MODELS) if provider == "llama" else "Use a model name such as nomic-embed-text.")
    cfg.update(enabled=payload["enabled"], model=model, provider=provider)
    semantic.save_config(Path(data_root), cfg)
    return status(data_root)


def pull(data_root: Path, payload: Any) -> dict[str, Any]:
    """Download the configured model through the local service. The only operation that uses the network."""
    if not isinstance(payload, dict) or set(payload) - {"confirm"} or payload.get("confirm") is not True:
        raise _bad("explicit confirmation required", "Send {confirm: true}.")
    cfg = semantic.load_config(data_root)
    if not cfg["enabled"]:
        raise MemoryOpError("SEMANTIC_OFF", "Semantic search is not enabled.", "Enable it first.")
    _wrap(lambda: semantic.pull_model(Path(data_root), cfg))
    return status(data_root)
