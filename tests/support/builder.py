"""packaging/ is not a package (it would shadow pip's `packaging`), so the build script is loaded by path."""
import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("build_dist", Path(__file__).resolve().parents[2] / "packaging/build_dist.py")
build_dist = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build_dist)
