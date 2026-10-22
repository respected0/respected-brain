#!/usr/bin/env python3
"""Run one of the product's own lifecycle operations against a program the smoke already laid down."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path

from respected_brain.core.config import ConfigStore
from respected_brain.core.paths import Roots
from respected_brain.integrations.backend import NativeBackend
from respected_brain.installation.repair import repair
from respected_brain.installation.setup import setup
from respected_brain.installation.uninstall import uninstall
from respected_brain.vault.registry import build_context


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("setup", "repair", "uninstall"))
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--vault", type=Path, required=True)
    parser.add_argument("--vault-id")
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--summary-provider", default="claude")
    args = parser.parse_args()
    if args.action != "setup" and not args.vault_id:
        parser.error("--vault-id is required outside setup")

    roots = Roots(args.app_root.resolve(), args.data_root.resolve(), args.vault.resolve())
    backend = NativeBackend(roots.data_root, user_home=args.home.resolve())
    if args.action == "setup":
        result = setup(roots, roots.default_vault, backend=backend,
                       values={"user_name": "Smoke User", "assistant_name": "Smoke Companion", "summary_provider": args.summary_provider},
                       platform="windows-native" if os.name == "nt" else "posix", home=args.home.resolve())
    else:
        ctx = build_context(roots, ConfigStore(roots.data_root), vault=None, vault_id=args.vault_id, env={})
        result = repair(ctx, backend=backend) if args.action == "repair" else uninstall(ctx, backend=backend)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
