"""Automatic search-index freshness: incremental refresh run by the product's own hook/schedule processes (no Hub, no daemon)."""

from __future__ import annotations

import sqlite3
import time
from typing import Any

from ..core.context import AppContext
from ..core.errors import BusyError
from .engine import SearchEngine



def refresh_now(ctx: AppContext, *, attempts: int = 5, wait: float = 2.0) -> dict[str, Any]:
    """Incremental refresh (sha256 based); retries while another writer holds the lease."""
    for attempt in range(attempts):
        try:
            stats = SearchEngine(ctx).index_vault()
        except BusyError:  # another writer is admitted right now: same as a busy index, wait and retry
            stats = None
        except (ValueError, OSError, sqlite3.Error) as error:  # freshness is best effort: never fail the caller's real work
            return {"refreshed": False, "reason": type(error).__name__}
        if stats is not None:
            return {"refreshed": True, **stats, "semantic": refresh_semantic(ctx)}
        if attempt + 1 < attempts:
            time.sleep(wait)
    return {"refreshed": False, "reason": "busy"}


def refresh_semantic(ctx: AppContext) -> dict[str, Any]:
    """Best-effort vector update after an FTS refresh; silent no-op unless the user enabled semantic search."""
    from . import semantic
    cfg = semantic.load_config(ctx.paths.data_root)
    if not cfg["enabled"]:
        return {"state": "off"}
    try:
        return {"state": "ok", **semantic.build(ctx, cfg, SearchEngine(ctx))}
    except semantic.SemanticError as error:
        return {"state": "unavailable", "code": error.code}
    except (OSError, ValueError):
        return {"state": "unavailable", "code": "INTERNAL"}
