"""MCP süreci içinde çalışan yoklama tabanlı dizin tazeleyici; ayrı süreç ya da servis yoktur."""

from __future__ import annotations

import sqlite3
import threading
import time
from typing import Callable

from ..core.errors import BusyError
from .engine import SearchEngine


class SearchIndexWatcher:
    """Uzun ömürlü MCP sürecinde kasayı yoklar; yalnızca FTS dizinini tazeler, anlamsal vektörleri kurmaz."""

    def __init__(self, engine: SearchEngine, *, interval: float = 1.0, debounce: float = 0.25,
                 large_vault_interval: float = 30.0,
                 clock: Callable[[], float] = time.monotonic) -> None:
        self.engine = engine
        self.interval = interval
        self.debounce = debounce
        self.large_vault_interval = large_vault_interval
        self._clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._writing = threading.Lock()
        self._stale_since: float | None = None
        self._next_unknown = 0.0

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="respected-index-watch", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        thread, self._thread = self._thread, None
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=12.0)  # index_vault waits at most 10 s for the writer lease

    def _run(self) -> None:
        while not self._stop.wait(self.interval):
            self.scan_once()

    def scan_once(self, now: float | None = None) -> bool:
        """Tek yoklama: değişiklik varsa debounce sonrası artımlı indeks yazar."""
        now = self._clock() if now is None else now
        try:
            state = self.engine.index_state()["state"]
        except (OSError, sqlite3.Error):
            self._stale_since = None
            return False
        if state == "fresh":
            self._stale_since = None
            return False
        if state == "unknown":
            if now < self._next_unknown:
                return False
        else:
            if self._stale_since is None:
                self._stale_since = now
                return False
            if now - self._stale_since < self.debounce:
                return False
        self._stale_since = None
        if not self._writing.acquire(blocking=False):
            return False
        try:
            result = self.engine.index_vault()
        except (BusyError, OSError, sqlite3.Error):
            self._stale_since = now
            return False
        finally:
            self._writing.release()
        if state == "unknown":
            self._next_unknown = now + self.large_vault_interval
        return result is not None
