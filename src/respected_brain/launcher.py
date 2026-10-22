"""The installed program's first step: an RPP call is answered without importing the whole command line (argparse, vault registry, settings)."""
from __future__ import annotations

import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if args == ["rpp"]:
        from .core.platform import prepare_process
        prepare_process()
        from .rpp.server import main as rpp_main
        return rpp_main()
    from .cli import main as command_line
    return command_line(argv)
