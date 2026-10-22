"""RPP `memory.capture.run`: process pending AI sessions now (the manual counterpart of capture_mode = manual)."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..providers.runner import ModelRunner
from .integrations import _context
from .memory import MemoryOpError, _active_vault_id, _bad


def run(data_root: Path, payload: Any) -> dict[str, Any]:
    """Summarise finished, not yet captured sessions of every supported AI client and compile changed days."""
    if not isinstance(payload, dict) or set(payload) != {"confirm"} or payload["confirm"] is not True:
        raise _bad("explicit confirmation required", "Send {confirm: true}.")
    if not _active_vault_id(Path(data_root)):
        raise MemoryOpError("NO_VAULT", "No vault is registered.", "Register a vault in the Brain product first.")
    from ..memory.flush import catch_up_unflushed_sessions, compile_catch_up
    _, ctx = _context(Path(data_root), {})
    now = datetime.now().astimezone()
    model = ModelRunner(ctx)
    captured = catch_up_unflushed_sessions(ctx, model=model, now=now, home=Path.home())
    captured += _flush_pending(ctx, model, now)
    compiled = compile_catch_up(ctx, model=model, now=now)
    return {"captured_sessions": captured, "compile_status": compiled, "pending_left": len(list(ctx.paths.state_dir.glob("pending-capture-*.json")))}


def _flush_pending(ctx, model, now) -> int:
    """Sessions that ended while capture_mode was manual (their hook payloads were kept, nothing else)."""
    from ..memory.flush import flush_transcript
    done = 0
    for pending in sorted(ctx.paths.state_dir.glob("pending-capture-*.json"), key=lambda p: p.stat().st_mtime):
        try:
            item = json.loads(pending.read_text(encoding="utf-8"))
            payload = item["payload"]
            status = flush_transcript(ctx, session_id=payload["session_id"], transcript=Path(payload["transcript_path"]), model=model,
                                      now=now, reason=item.get("reason", "sessionend"), hook_payload=payload)
        except (OSError, ValueError, KeyError, TypeError):
            continue  # unreadable record or missing transcript: left for the user to see, never deleted blindly
        if status == 0:
            pending.unlink(missing_ok=True)
            done += 1
    return done
