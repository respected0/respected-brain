"""Test packages; product imports use the installed respectedbrain package.

Importing this package (unittest discovery does it before any test module) points HOME, USERPROFILE, APPDATA and
LOCALAPPDATA at a fresh empty folder, so no test can reach the real AI-client configuration, vault registry or
scheduled-task state of the person running the suite, whatever runner is used. Child processes inherit it.
"""
import atexit
import os
from pathlib import Path
import shutil
import tempfile

if not os.environ.get("RESPECTED_TEST_SANDBOX"):
    _home = Path(tempfile.mkdtemp(prefix="respected-test-home-"))
    for _sub in ("AppData/Roaming", "AppData/Local"):
        (_home / _sub).mkdir(parents=True)
    os.environ.update(USERPROFILE=str(_home), HOME=str(_home), APPDATA=str(_home / "AppData/Roaming"),
                      LOCALAPPDATA=str(_home / "AppData/Local"), RESPECTED_TEST_SANDBOX=str(_home))
    os.environ.setdefault("PYTHONUTF8", "1")
    atexit.register(shutil.rmtree, _home, ignore_errors=True)
