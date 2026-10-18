"""Optional local semantic search layered on the FTS index (never required; FTS keeps working without it).

Embeddings are computed on THIS machine. Default provider "llama": a pinned llama.cpp `llama-server` plus a pinned GGUF
model, downloaded on explicit request into the data root (`semantic-runtime/`) and started only for the duration of one
operation on a loopback port (no resident process). Alternative provider "ollama": an Ollama the user already runs.
Any non-loopback endpoint is refused, so vault text never leaves the computer. Vectors live in their own SQLite file next
to the FTS index and can be deleted at any time.
shortcut: one vector per note (title + first 2000 characters) and a linear cosine scan, fine for tens of thousands of
notes; the runtime is Windows x64 only (other platforms use provider ollama); move to chunking/ANN when needed.
"""

from __future__ import annotations

import array
import hashlib
import json
import math
import os
import shutil
import socket
import sqlite3
import subprocess
import time
import urllib.error
import urllib.request
import zipfile
from contextlib import closing, contextmanager
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from ..core import platform as runtime_platform
from ..core.config import atomic_write_json
from ..core.context import AppContext
from ..core.coordination import writer_lease

CONFIG_FILE = "semantic.json"
DB_NAME = "semantic_index.db"
DEFAULT = {"enabled": False, "provider": "llama", "model": "bge-m3-Q4_K_M", "endpoint": "http://127.0.0.1:11434"}
PROVIDERS = ("llama", "ollama")
# Pinned downloads (sha256 verified before use). Only these URLs are ever fetched, only by `pull`.
RUNTIME = {"url": "https://github.com/ggml-org/llama.cpp/releases/download/b11669/llama-b11669-bin-win-cpu-x64.zip",
           "sha256": "37b3efcf962847ca869745fd4ccf7f5e7e8dacfeff9fa3523b4ca8cdc66d632b", "size": 19537886, "exe": "llama-server.exe"}
MODELS = {"bge-m3-Q4_K_M": {"url": "https://huggingface.co/gpustack/bge-m3-GGUF/resolve/main/bge-m3-Q4_K_M.gguf",
                            "sha256": "6d39681b26c61279ac1f82db35a04a05009e94c415b51c858ff571489a82fc06", "size": 437778496}}
DOWNLOAD_MB = round((RUNTIME["size"] + MODELS["bge-m3-Q4_K_M"]["size"]) / 1e6)
_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
_MAX_CHARS = 2000
_BATCH = 16


class SemanticError(Exception):
    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code, self.message, self.hint = code, message, hint


def check_endpoint(url: Any) -> str:
    parsed = urlparse(url) if isinstance(url, str) else None
    if not parsed or parsed.scheme != "http" or parsed.hostname not in _LOOPBACK or parsed.path not in ("", "/") or parsed.username:
        raise SemanticError("BAD_REQUEST", "Only a local (loopback) http endpoint is allowed.", "Vault text must not leave this computer.")
    return f"http://{parsed.hostname if parsed.hostname != '::1' else '[::1]'}:{parsed.port or 11434}"


def load_config(data_root: Path) -> dict[str, Any]:
    try:
        stored = json.loads((Path(data_root) / CONFIG_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        stored = {}
    cfg = dict(DEFAULT)
    if isinstance(stored, dict):
        cfg.update({k: stored[k] for k in DEFAULT if k in stored})
    if (not isinstance(cfg["enabled"], bool) or cfg["provider"] not in PROVIDERS
            or not isinstance(cfg["model"], str) or not cfg["model"]
            or (cfg["provider"] == "llama" and cfg["model"] not in MODELS)):
        return dict(DEFAULT)
    try:
        cfg["endpoint"] = check_endpoint(cfg["endpoint"])
    except SemanticError:
        return dict(DEFAULT)
    return cfg


def save_config(data_root: Path, cfg: dict[str, Any]) -> None:
    atomic_write_json(Path(data_root) / CONFIG_FILE, {k: cfg[k] for k in DEFAULT})


def _paths(data_root: Path, cfg: dict[str, Any]) -> tuple[Path, Path]:
    base = Path(data_root) / "semantic-runtime"
    return base / "llama" / RUNTIME["exe"], base / "models" / f"{cfg['model']}.gguf"


def _model_ok(path: Path, cfg: dict[str, Any]) -> bool:
    try:
        return path.is_file() and path.stat().st_size == MODELS[cfg["model"]]["size"]
    except (OSError, KeyError):
        return False


def _call(endpoint: str, path: str, body: dict[str, Any] | None = None, timeout: float = 5.0) -> Any:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(check_endpoint(endpoint) + path, data=data, headers={"Content-Type": "application/json"} if data else {})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 loopback only (check_endpoint)
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError, TimeoutError) as exc:
        raise SemanticError("PROVIDER_UNAVAILABLE", "The local embedding service is not reachable.",
                            "Enable semantic search again from the Hub.") from exc


def provider_state(data_root: Path, cfg: dict[str, Any]) -> dict[str, Any]:
    if cfg["provider"] == "llama":
        exe, model = _paths(data_root, cfg)
        return {"provider": "up" if exe.is_file() else "down", "model_installed": _model_ok(model, cfg)}
    try:
        tags = _call(cfg["endpoint"], "/api/tags", timeout=2.0)
    except SemanticError:
        return {"provider": "down", "model_installed": False}
    names = [m.get("name", "") for m in tags.get("models", []) if isinstance(m, dict)]
    return {"provider": "up", "model_installed": any(n == cfg["model"] or n.startswith(cfg["model"] + ":") for n in names)}


def _download(url: str, target: Path, sha256: str, size: int) -> None:
    """Fetch a pinned file next to its target, verify size and sha256, then move it into place."""
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".part")
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "respectedbrain"}), timeout=60) as response, temporary.open("wb") as out:  # noqa: S310 pinned https URL
            while chunk := response.read(1 << 20):
                digest.update(chunk)
                out.write(chunk)
        if temporary.stat().st_size != size or digest.hexdigest() != sha256:
            raise SemanticError("DOWNLOAD_CORRUPT", "The downloaded file did not match its expected checksum.", "Try again; nothing was installed.")
        os.replace(temporary, target)
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SemanticError("DOWNLOAD_FAILED", "The download failed.", "Check the internet connection and try again.") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _extract(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as bundle:
        for info in bundle.infolist():
            target = (destination / info.filename).resolve()
            if root not in target.parents and target != root:
                raise SemanticError("DOWNLOAD_CORRUPT", "The runtime archive contains an unsafe path.", "Nothing was installed.")
        bundle.extractall(destination)


def pull_model(data_root: Path, cfg: dict[str, Any]) -> None:
    """Install the runtime and model (provider llama) or ask the local Ollama to download it. The only network use."""
    if cfg["provider"] == "ollama":
        reply = _call(cfg["endpoint"], "/api/pull", {"model": cfg["model"], "stream": False}, timeout=3600.0)
        if not isinstance(reply, dict) or reply.get("status") != "success":
            raise SemanticError("PULL_FAILED", "The model could not be downloaded.", "Check the model name and the connection.")
        return
    exe, model = _paths(data_root, cfg)
    if not exe.is_file():
        archive = exe.parent.parent / "runtime.zip"
        _download(RUNTIME["url"], archive, RUNTIME["sha256"], RUNTIME["size"])
        staging = exe.parent.with_name(exe.parent.name + ".part")  # an interrupted extraction must never leave a half runtime in place
        shutil.rmtree(staging, ignore_errors=True)
        try:
            _extract(archive, staging)
            if not (staging / exe.name).is_file():
                raise SemanticError("DOWNLOAD_CORRUPT", "The runtime archive did not contain the embedding server.", "Nothing was installed.")
            shutil.rmtree(exe.parent, ignore_errors=True)
            os.replace(staging, exe.parent)
        finally:
            archive.unlink(missing_ok=True)
            shutil.rmtree(staging, ignore_errors=True)
        if not exe.is_file():
            raise SemanticError("DOWNLOAD_CORRUPT", "The runtime archive did not contain the embedding server.", "Nothing was installed.")
    if not _model_ok(model, cfg):
        spec = MODELS[cfg["model"]]
        _download(spec["url"], model, spec["sha256"], spec["size"])


@contextmanager
def embedder(data_root: Path, cfg: dict[str, Any]):
    """Yield a config whose endpoint serves embeddings; for provider llama start the pinned server just for this operation."""
    if cfg["provider"] == "ollama":
        yield cfg
        return
    exe, model = _paths(data_root, cfg)
    if not exe.is_file() or not _model_ok(model, cfg):
        raise SemanticError("PROVIDER_UNAVAILABLE", "The local embedding model is not installed.", "Enable semantic search again from the Hub (downloads it).")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    process = subprocess.Popen([str(exe), "-m", str(model), "--embeddings", "--host", "127.0.0.1", "--port", str(port), "-c", "8192", "-np", "4"],
                               cwd=exe.parent, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               **runtime_platform.hidden_process_options())
    endpoint = f"http://127.0.0.1:{port}"
    try:
        deadline = time.monotonic() + 180
        while True:
            if process.poll() is not None:
                raise SemanticError("RUNTIME_FAILED", "The embedding server stopped while starting.", "Enable semantic search again from the Hub.")
            try:
                _call(endpoint, "/health", timeout=2.0)
                break
            except SemanticError:
                if time.monotonic() > deadline:
                    raise SemanticError("RUNTIME_FAILED", "The embedding server did not become ready.", "Try again.") from None
                time.sleep(0.5)
        yield {**cfg, "endpoint": endpoint}
    finally:
        process.terminate()
        try:
            process.wait(10)
        except subprocess.TimeoutExpired:
            process.kill()


def embed(cfg: dict[str, Any], texts: list[str], timeout: float = 120.0) -> list[list[float]]:
    if cfg["provider"] == "llama":
        reply = _call(cfg["endpoint"], "/v1/embeddings", {"input": texts, "model": cfg["model"]}, timeout=timeout)
        rows = sorted(reply.get("data", []), key=lambda r: r.get("index", 0)) if isinstance(reply, dict) else []
        vectors = [r.get("embedding") for r in rows if isinstance(r, dict)]
    else:
        reply = _call(cfg["endpoint"], "/api/embed", {"model": cfg["model"], "input": texts}, timeout=timeout)
        vectors = reply.get("embeddings") if isinstance(reply, dict) else None
    if (not isinstance(vectors, list) or len(vectors) != len(texts)
            or not all(isinstance(v, list) and v and all(isinstance(x, (int, float)) for x in v) for v in vectors)):
        raise SemanticError("PROVIDER_BAD_REPLY", "The embedding service returned an unexpected reply.", "")
    return vectors


def _db(ctx: AppContext) -> Path:
    return ctx.paths.cache_dir / DB_NAME


def _pack(vector: list[float]) -> bytes:
    norm = math.sqrt(sum(x * x for x in vector)) or 1.0
    return array.array("f", (x / norm for x in vector)).tobytes()


def vector_count(ctx: AppContext, model: str) -> int:
    path = _db(ctx)
    if not path.is_file():
        return 0
    try:
        with closing(sqlite3.connect("file:" + path.as_posix() + "?mode=ro", uri=True)) as con:
            return con.execute("SELECT COUNT(*) FROM vec WHERE model = ?", (model,)).fetchone()[0]
    except sqlite3.Error:
        return 0


def build(ctx: AppContext, cfg: dict[str, Any], engine) -> dict[str, int]:
    """Embed new/changed notes of the FTS index; drop vectors of removed ones. Raises SemanticError when the service is unusable."""
    if not cfg["enabled"]:
        return {"embedded": 0, "kept": 0, "removed": 0}
    state = provider_state(ctx.paths.data_root, cfg)
    if state["provider"] != "up" or not state["model_installed"]:
        raise SemanticError("PROVIDER_UNAVAILABLE", "The local embedding model is not ready.", "Enable it again from the Hub (downloads the model).")
    with engine._get_connection() as fts:
        rows = [(r["rel_path"], r["sha256"], r["title"]) for r in fts.execute("SELECT rel_path, sha256, title FROM files_meta")]
    with writer_lease(ctx):
        _db(ctx).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(str(_db(ctx)))) as con:
            con.execute("CREATE TABLE IF NOT EXISTS vec (rel_path TEXT PRIMARY KEY, sha256 TEXT NOT NULL, model TEXT NOT NULL, dim INTEGER NOT NULL, v BLOB NOT NULL)")
            have = {r[0]: (r[1], r[2]) for r in con.execute("SELECT rel_path, sha256, model FROM vec")}
            todo, kept = [], 0
            for rel, sha, title in rows:
                if have.get(rel) == (sha, cfg["model"]):
                    kept += 1
                else:
                    todo.append((rel, sha, title))
            embedded = 0
            if todo:
                with embedder(ctx.paths.data_root, cfg) as live:
                    for i in range(0, len(todo), _BATCH):
                        batch, texts = [], []
                        for rel, sha, title in todo[i:i + _BATCH]:
                            try:
                                data = (ctx.paths.vault_root / rel).read_bytes()
                            except OSError:
                                continue
                            if hashlib.sha256(data).hexdigest() != sha:
                                continue  # edited since the FTS pass; the next refresh handles it
                            batch.append((rel, sha))
                            texts.append(f"{title}\n{data.decode('utf-8', 'replace')[:_MAX_CHARS]}")
                        if not texts:
                            continue
                        for (rel, sha), vector in zip(batch, embed(live, texts)):
                            con.execute("INSERT OR REPLACE INTO vec VALUES (?, ?, ?, ?, ?)", (rel, sha, cfg["model"], len(vector), _pack(vector)))
                            embedded += 1
                        con.commit()
            liverel = {rel for rel, _, _ in rows}
            gone = [rel for rel in have if rel not in liverel]
            con.executemany("DELETE FROM vec WHERE rel_path = ?", [(rel,) for rel in gone])
            con.commit()
    return {"embedded": embedded, "kept": kept, "removed": len(gone)}


def search(ctx: AppContext, cfg: dict[str, Any], query: str, limit: int) -> list[tuple[str, float]]:
    """Cosine ranking of the stored vectors for the query. Read-only; raises SemanticError if the service is unusable."""
    path = _db(ctx)
    if not path.is_file():
        raise SemanticError("SEMANTIC_NOT_BUILT", "No semantic vectors yet.", "Refresh the memory index.")
    with embedder(ctx.paths.data_root, cfg) as live:
        (qv,) = embed(live, [query], timeout=30.0)
    q = array.array("f", [float(x) for x in qv])
    norm = math.sqrt(sum(x * x for x in q)) or 1.0
    scored: list[tuple[str, float]] = []
    with closing(sqlite3.connect("file:" + path.as_posix() + "?mode=ro", uri=True)) as con:
        for rel, dim, blob in con.execute("SELECT rel_path, dim, v FROM vec WHERE model = ?", (cfg["model"],)):
            if dim != len(q):
                continue
            v = array.array("f")
            v.frombytes(blob)
            scored.append((rel, sum(a * b for a, b in zip(q, v)) / norm))
    scored.sort(key=lambda item: -item[1])
    return scored[:limit]
