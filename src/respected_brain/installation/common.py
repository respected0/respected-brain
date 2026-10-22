"""Shared installation context and integration profile construction."""
from pathlib import Path
import sys
from respected_brain.core.context import AppContext
from respected_brain.core.paths import AppPaths
from respected_brain.core.resources import ResourceCatalog
from respected_brain.integrations.backend import IntegrationProfile


def installed_profile(roots, profile):
    name = profile.get("platform", "windows-native" if sys.platform == "win32" else "posix")
    if name not in ("windows-native", "posix", "windows-wsl"):
        raise ValueError("Unknown integration platform")
    if name == "windows-native":
        launcher = (str(roots.app_root / "respected-brain.exe"),)
    elif name == "windows-wsl":
        launcher = ("respected-brain",)
    elif sys.platform == "darwin":
        launcher = (str(roots.app_root / "Contents/MacOS/respected-brain"),)
    else:
        launcher = (str(roots.app_root / "respected-brain"),)
    home = Path(profile.get("user_home", str(Path.home())))
    if not home.is_absolute():
        raise ValueError("Integration user_home must be absolute")
    return IntegrationProfile(name, launcher, home)


def installation_context(roots, vault, identity, config):
    return AppContext(AppPaths(roots.app_root, roots.data_root, vault, identity), config, ResourceCatalog())


def linux_launcher_path(ctx, profile):
    from .ownership import safe_path
    from respected_brain.core.errors import OwnershipConflict
    home = safe_path(profile.user_home)
    if not home.is_dir():
        raise OwnershipConflict("Linux launcher home must exist")
    target = safe_path(home / ".local/bin/respected-brain")
    for root in (ctx.paths.app_root, ctx.paths.data_root, ctx.paths.vault_root):
        if target.is_relative_to(root) or root.is_relative_to(target):
            raise OwnershipConflict("Linux PATH launcher exceeds the installation boundary")
    return target


def ensure_linux_launcher(ctx, profile, tx, previous):
    """Install the required PATH entry independently of optional integrations."""
    import json
    import shlex
    import stat
    from .ownership import OwnedFile, digest, prove_ownership
    from respected_brain.core.errors import OwnershipConflict
    if not sys.platform.startswith("linux") or profile.platform != "posix":
        return ()
    document = json.loads((ctx.paths.app_root / "distribution.json").read_text(encoding="utf-8"))
    if document.get("platform") != "linux":
        return ()
    target = linux_launcher_path(ctx, profile)
    if target.exists() and (target.stat().st_nlink != 1 or not prove_ownership(target, previous)):
        raise OwnershipConflict(f"Linux PATH launcher is unowned or changed: {target}")
    executable = ctx.paths.app_root / document["launcher"]
    content = ("#!/bin/sh\nexec " + shlex.quote(str(executable)) + ' "$@"\n').encode("utf-8")
    tx.write(target, content, mode=0o755)
    return (OwnedFile(target, digest(target), "launcher", stat.S_IMODE(target.stat().st_mode)),)
