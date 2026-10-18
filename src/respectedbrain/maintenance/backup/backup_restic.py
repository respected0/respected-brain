#!/usr/bin/env python3
"""Opt-in, verified Restic backup and restore utility for Respected Brain vaults.

    backup:  backup_restic --repo REPO [--password-file FILE] [--apply]
    restore: backup_restic --repo REPO --restore-to NEW_EMPTY_FOLDER [--snapshot ID|latest] [--password-file FILE]

A restore never touches the vault: it writes into a new (or empty) folder outside it and reports where the vault copy is, so
the user decides what to copy back. Backups are verified by restoring them and comparing every file's SHA-256 with the vault.
"""

from __future__ import annotations

from respectedbrain.core.context import AppContext
from respectedbrain.maintenance import selected_vault, mutable_target

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any

_SKIP = {".git", ".obsidian", "__pycache__"}


def check_prerequisites() -> tuple[bool, str]:
    """Verify that restic CLI is installed on the host."""
    binary = shutil.which("restic") or shutil.which("restic.exe")
    if binary is None:
        return False, "Restic kurulu değil. Lütfen kurun (Windows: winget/scoop/choco install restic, macOS: brew install restic, Linux: apt install restic)."
    return True, binary


def check_target_safety(vault_root: Path, repo_target: str) -> None:
    """Ensure repo target is not inside the vault itself."""
    is_inside = False
    try:
        target_path = Path(repo_target).resolve()
        is_inside = (target_path == vault_root or target_path.is_relative_to(vault_root))
    except (ValueError, OSError):
        is_inside = False

    if is_inside:
        raise ValueError("Yedek deposu (repo target) vault içinde olamaz.")


def _environment(repo_target: str, password: str | None, password_file: Path | None) -> dict[str, str] | None:
    env = os.environ.copy()
    if password:
        env["RESTIC_PASSWORD"] = password
    if password_file:
        env["RESTIC_PASSWORD_FILE"] = str(password_file)
    env["RESTIC_REPOSITORY"] = repo_target
    if not (env.get("RESTIC_PASSWORD") or env.get("RESTIC_PASSWORD_FILE")):
        return None
    return env


NO_PASSWORD = {"status": "error", "error": "Restic deposu için parola yok: RESTIC_PASSWORD, RESTIC_PASSWORD_FILE veya --password-file verin."}


def _tree_digest(root: Path, *, not_after: float | None = None) -> dict[str, str]:
    """relative path -> sha256 of every regular file (links skipped); with not_after only files unchanged since then."""
    digests: dict[str, str] = {}
    for directory, names, files in os.walk(root, followlinks=False):
        names[:] = [name for name in names if name not in _SKIP and not (Path(directory) / name).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.is_symlink() or (not_after is not None and path.stat().st_mtime > not_after):
                continue
            digests[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return digests


def _snapshot_path(path: str) -> str:
    """restic's own spelling of a saved absolute path (Windows drive paths become /C/x/y); used as `snapshot:/subfolder`."""
    text = path.replace(chr(92), "/")
    return "/" + text.replace(":", "", 1).lstrip("/") if len(text) > 1 and text[1] == ":" else text


def _verify_restored(restored: Path, vault_root: Path, started: float) -> list[str]:
    """Problems found comparing the restored copy with the vault (files changed after the backup began are ignored)."""
    expected = _tree_digest(vault_root, not_after=started)
    actual = _tree_digest(restored)
    problems = [f"missing: {name}" for name in sorted(expected) if name not in actual]
    problems += [f"different: {name}" for name in sorted(expected) if name in actual and actual[name] != expected[name]]
    return problems[:20]


def run_backup(
    vault_root: Path,
    repo_target: str,
    password: str | None = None,
    verify_restore: bool = True,
    apply: bool = False,
    *, temp_dir: Path | None = None, password_file: Path | None = None,
) -> dict[str, Any]:
    """Execute restic backup and optionally verify the snapshot by restoring it and comparing file contents."""
    ready, message = check_prerequisites()
    if not ready:
        return {"status": "error", "error": message}

    try:
        check_target_safety(vault_root, repo_target)
    except ValueError as exc:
        return {"status": "error", "error": str(exc)}

    env = _environment(repo_target, password, password_file)
    if env is None and apply:
        return dict(NO_PASSWORD)
    env = env or os.environ.copy()

    if not apply:
        return {
            "status": "preview",
            "vault": str(vault_root),
            "repo": repo_target,
            "verify_restore": verify_restore,
        }

    probe = subprocess.run(["restic", "cat", "config"], env=env, capture_output=True, text=True, check=False)
    if probe.returncode != 0:  # first run against a new repository
        created = subprocess.run(["restic", "init"], env=env, capture_output=True, text=True, check=False)
        if created.returncode != 0:
            return {"status": "failed", "error": created.stderr or created.stdout}
    started = time.time()
    cmd = ["restic", "backup", str(vault_root), "--json"]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return {"status": "failed", "error": proc.stderr or proc.stdout}

    snapshot_id = None
    for line in reversed(proc.stdout.splitlines()):
        try:
            data = json.loads(line)
            if isinstance(data, dict) and data.get("message_type") == "summary" and isinstance(data.get("snapshot_id"), str) and data['snapshot_id']:
                snapshot_id = data["snapshot_id"]
                break
        except (json.JSONDecodeError, ValueError):
            continue
    if snapshot_id is None:
        return {"status": "failed", "error": "Backup did not identify its snapshot; restore verification refused"}

    if verify_restore:
        if temp_dir is not None:
            temp_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_dir) as verify_dir:
            # `snapshot:/vault/path` restores only the vault's content: a plain restore recreates C:\Users\... and restic then
            # fails on the read-only system folders in that chain (observed with restic 0.19.1 on Windows).
            restore_cmd = ["restic", "restore", f"{snapshot_id}:{_snapshot_path(str(vault_root))}", "--target", verify_dir]
            r_proc = subprocess.run(restore_cmd, env=env, capture_output=True, text=True, check=False)
            if r_proc.returncode != 0:
                return {"status": "verify-failed", "error": r_proc.stderr, "snapshot_id": snapshot_id}
            problems = _verify_restored(Path(verify_dir), vault_root, started)
            if problems:
                return {"status": "verify-failed", "error": "; ".join(problems), "snapshot_id": snapshot_id}

    return {"status": "ok", "snapshot_id": snapshot_id}


def run_restore(
    repo_target: str, restore_to: Path, vault_root: Path | None = None, *, snapshot: str = "latest",
    password: str | None = None, password_file: Path | None = None,
) -> dict[str, Any]:
    """Restore a snapshot into a NEW or EMPTY folder outside the vault; never overwrites the vault or anything else."""
    ready, message = check_prerequisites()
    if not ready:
        return {"status": "error", "error": message}
    if not isinstance(snapshot, str) or not (snapshot == "latest" or snapshot.isalnum()):
        return {"status": "error", "error": "Geçersiz anlık görüntü (snapshot) kimliği."}
    restore_to = Path(restore_to)
    if not restore_to.is_absolute():
        return {"status": "error", "error": "Geri yükleme klasörü mutlak yol olmalı."}
    try:
        resolved = restore_to.resolve()
        if vault_root is not None and (resolved == vault_root or resolved.is_relative_to(vault_root) or vault_root.is_relative_to(resolved)):
            return {"status": "error", "error": "Geri yükleme klasörü vault ile iç içe olamaz; vault'un üzerine yazılmaz."}
        if restore_to.exists() and (not restore_to.is_dir() or any(restore_to.iterdir())):
            return {"status": "error", "error": "Geri yükleme klasörü yeni olmalı veya boş olmalı."}
        if any(part.is_symlink() for part in (restore_to, *restore_to.parents) if part.exists()):
            return {"status": "error", "error": "Geri yükleme yolunda bağlantı (link) olamaz."}
    except OSError as exc:
        return {"status": "error", "error": str(exc)}
    env = _environment(repo_target, password, password_file)
    if env is None:
        return dict(NO_PASSWORD)
    restore_to.mkdir(parents=True, exist_ok=True)
    listed = subprocess.run(["restic", "snapshots", snapshot, "--json"], env=env, capture_output=True, text=True, check=False)
    try:
        saved = json.loads(listed.stdout)[-1]
        source = saved["paths"][0]
        spec = f"{saved['id']}:{_snapshot_path(source)}"
    except (ValueError, KeyError, IndexError, TypeError):
        restore_to.rmdir() if restore_to.is_dir() and not any(restore_to.iterdir()) else None
        return {"status": "failed", "error": listed.stderr or "Anlık görüntü bulunamadı."}
    done = subprocess.run(["restic", "restore", spec, "--target", str(restore_to)], env=env, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        return {"status": "failed", "error": done.stderr or done.stdout}
    count = sum(len(files) for _, _, files in os.walk(restore_to))
    if count == 0:
        return {"status": "failed", "error": "Geri yüklenen klasörde dosya yok."}
    return {"status": "ok", "restored_to": str(restore_to), "files": count,
            "note": "Vault'unuza dokunulmadı. Gerekli dosyaları bu klasörden kendiniz geri kopyalayın."}


def main(argv: list[str] | None = None, *, ctx: AppContext | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("vault", type=Path, nargs="?", help="Vault kök dizini")
    parser.add_argument("--repo", required=True, help="Restic repository konumu")
    parser.add_argument("--apply", action="store_true", help="Yedeklemeyi gerçekten çalıştır")
    parser.add_argument("--password-file", type=Path, help="Restic parolasını içeren dosya (yoksa RESTIC_PASSWORD kullanılır)")
    parser.add_argument("--skip-verify", action="store_true", help="Restore doğrulamasını atla")
    parser.add_argument("--restore-to", type=Path, help="Anlık görüntüyü bu YENİ/boş klasöre geri yükle (vault'a dokunmaz)")
    parser.add_argument("--snapshot", default="latest", help="Geri yüklenecek anlık görüntü kimliği (varsayılan: latest)")
    args = parser.parse_args(argv)

    if Path(args.repo).is_absolute():
        mutable_target(ctx, Path(args.repo))
    vault = selected_vault(ctx, args.vault)
    if args.restore_to is not None:
        result = run_restore(args.repo, args.restore_to, vault, snapshot=args.snapshot, password_file=args.password_file)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("status") == "ok" else 1
    result = run_backup(
        vault_root=vault,
        repo_target=args.repo,
        temp_dir=ctx.paths.cache_dir if ctx else None,
        verify_restore=not args.skip_verify,
        apply=args.apply,
        password_file=args.password_file,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status") in {"ok", "preview"} else 1


if __name__ == "__main__":
    sys.exit(main())
