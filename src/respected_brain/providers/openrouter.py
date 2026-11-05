"""OpenRouter direct API adapter and OS-bound API key storage.

The key never enters config.json, prompts, errors or the usage ledger. Windows uses DPAPI; other
platforms use a 0600 file, which is only as strong as the user's home directory permissions.
"""

from __future__ import annotations

import ctypes
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

from ..core.config import atomic_write_bytes


ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"
PROTECTED = b"RBOR1D\0"
PLAIN = b"RBOR1P\0"
MAX_RESPONSE = 2 * 1024 * 1024


class CredentialError(Exception):
    """A safe, key-free credential failure."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def credential_path(data_root: Path) -> Path:
    return data_root / "credentials" / "openrouter.bin"


class _DataBlob(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_char))]


def _blob(data: bytes) -> tuple[_DataBlob, ctypes.Array]:
    buffer = ctypes.create_string_buffer(data, len(data))
    return _DataBlob(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char))), buffer


def _dpapi(data: bytes, *, protect: bool) -> bytes:
    if os.name != "nt":
        raise CredentialError("openrouter-key-unreadable")
    crypt32, kernel32 = ctypes.windll.crypt32, ctypes.windll.kernel32
    incoming, buffer = _blob(data)
    outgoing = _DataBlob()
    if protect:
        ok = crypt32.CryptProtectData(
            ctypes.byref(incoming), "respected-brain", None, None, None, 1, ctypes.byref(outgoing)
        )
    else:
        ok = crypt32.CryptUnprotectData(
            ctypes.byref(incoming), None, None, None, None, 1, ctypes.byref(outgoing)
        )
    if not ok:
        raise CredentialError("openrouter-key-unreadable")
    try:
        return ctypes.string_at(outgoing.pbData, outgoing.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(outgoing.pbData, ctypes.c_void_p))
        del buffer


def store_key(data_root: Path, key: str) -> None:
    key = key.strip()
    if not key or any(character in key for character in "\r\n\0"):
        raise ValueError("OpenRouter API anahtari bos ya da gecersiz")
    payload = PROTECTED + _dpapi(key.encode("utf-8"), protect=True) if os.name == "nt" else PLAIN + key.encode("utf-8")
    try:
        atomic_write_bytes(credential_path(data_root), payload, mode=0o600)  # shortcut: POSIX relies on home permissions, move to a keyring once one is a product dependency
    except OSError as error:
        raise CredentialError("openrouter-key-store-failed") from error


def load_key(data_root: Path) -> str | None:
    environment = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if environment:
        return environment
    path = credential_path(data_root)
    if not path.is_file():
        return None
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise CredentialError("openrouter-key-unreadable") from error
    if payload.startswith(PROTECTED):
        raw = _dpapi(payload[len(PROTECTED):], protect=False)
    elif payload.startswith(PLAIN) and os.name != "nt":
        raw = payload[len(PLAIN):]
    else:
        raise CredentialError("openrouter-key-unreadable")
    key = raw.decode("utf-8", errors="strict").strip()
    if not key:
        raise CredentialError("openrouter-key-unreadable")
    return key


def clear_key(data_root: Path) -> None:
    credential_path(data_root).unlink(missing_ok=True)


def status(data_root: Path) -> dict[str, object]:
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        return {"configured": True, "source": "environment"}
    path = credential_path(data_root)
    result: dict[str, object] = {"configured": path.is_file(), "source": "file" if path.is_file() else None}
    if path.is_file():
        try:
            result["protection"] = "dpapi" if path.read_bytes().startswith(PROTECTED) else "file-0600"
        except OSError:
            result["protection"] = "unreadable"
    return result


def _usage(state_dir: Path | None, model: str, usage: dict) -> None:
    if state_dir is None:
        return
    record = {
        "at": datetime.now(timezone.utc).isoformat(),
        "provider": "openrouter",
        "model": model,
        **{key: usage[key] for key in ("prompt_tokens", "completion_tokens", "total_tokens", "cost") if key in usage},
    }
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        with (state_dir / "provider-usage.jsonl").open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass  # cost telemetry must never fail or retry a paid call


def complete(
    prompt: str,
    *,
    data_root: Path,
    model: str = DEFAULT_MODEL,
    timeout: float = 120,
    endpoint: str = ENDPOINT,
    state_dir: Path | None = None,
) -> tuple[str | None, str | None]:
    """Make one chat completion; errors are bounded tags and never include the key or response body."""
    try:
        key = load_key(data_root)
    except CredentialError as error:
        return None, error.code
    if key is None:
        return None, "openrouter-key-missing"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=max(1.0, float(timeout))) as response:
            raw = response.read(MAX_RESPONSE + 1)
    except urllib.error.HTTPError as error:
        category = "auth" if error.code in (401, 403) else "payment" if error.code == 402 else "rate-limit" if error.code == 429 else "network" if error.code >= 500 else "http"
        return None, f"openrouter-http-{error.code}:{category}"
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return None, "openrouter-network" if not isinstance(error, TimeoutError) else "openrouter-timeout"
    if len(raw) > MAX_RESPONSE:
        return None, "openrouter-response-too-large"
    try:
        body = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        return None, "openrouter-invalid-response"
    if not isinstance(body, dict) or body.get("error"):
        return None, "openrouter-response-error"
    choices = body.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None, "openrouter-invalid-response"
    message = choices[0].get("message")
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        return None, "openrouter-empty-output"
    usage = body.get("usage")
    if isinstance(usage, dict):
        safe_usage = {
            key: value for key, value in usage.items()
            if key in ("prompt_tokens", "completion_tokens", "total_tokens") and isinstance(value, int)
        }
        cost = usage.get("cost")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            safe_usage["cost"] = float(cost)
        _usage(state_dir, model, safe_usage)
    return text.strip(), None
