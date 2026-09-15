# Failure Register

## Fixed and regression-tested

All eight product fixes below are contained in local commit `7762df945109cc8d7921a2865f5bad81d01aa43b` on `codex/v001-release-acceptance`.

1. **Codex notify chain destruction.** Normal uninstall deleted an outer computer-use notifier when Respected appeared as nested `--previous-notify` JSON without a chain file. Added a RED regression, implemented nested-argv surgery, then GREEN; unrelated TOML bytes stayed exact.
2. **Wrong shortcut cleanup name.** `uninstall.py main()` ignored `--vault-path` when choosing the shortcut name. Added RED/GREEN regression and passed two live uninstall runs.
3. **Wrong upstream repository.** Six launchers cloned `respected0/secondbrain` and used `secondbrain-main`. Behavior tests captured the real argv RED; all now target `respected0/respectedbrain` and `respectedbrain-main`, GREEN on Windows and WSL.
4. **Windows pipe-to-IEX failure.** Parameter `ValidateSet` rejected an existing empty `$Environment` variable before the script ran. Exact IEX regression was RED; manual post-binding validation is GREEN.
5. **POSIX piped `BASH_SOURCE` failure.** `curl | bash` referenced unset `BASH_SOURCE[0]`, then could use an unrelated current-directory installer. Exact stdin regression was RED; all three shell launchers now handle stdin mode and force download, GREEN.
6. **Current scheduler tasks survived uninstall.** The uninstaller searched only obsolete display strings and depended on localized LIST output. A CSV/no-header prefix regression was RED; current and legacy managed prefixes are now deleted independent of locale, unrelated tasks are retained, and the live residual count is zero.
7. **BOOTSTRAP reinstall was not idempotent.** A second run used `copytree(..., dirs_exist_ok=False)` and raised `FileExistsError`. A RED regression now installs twice while hashing a user file; recognized vaults route through the safe updater, unknown non-empty targets still fail closed, and the test is GREEN on Windows and WSL.
8. **Purge could report false success.** `shutil.rmtree(..., ignore_errors=True)` could leave a vault behind and still print that it was deleted. A RED no-op-removal regression now requires a nonzero exit and explicit error while the target exists; permission recovery and post-delete existence verification are GREEN. The exact live disposable purge was rerun and removed the residual tree.

## Unresolved release failures

- **Published Windows one-liner — FAILED.** The fixed `install.ps1` is only on the local branch; raw GitHub `main` still has the pipe-to-IEX defect.
- **Published POSIX one-liner — FAILED.** The fixed shell launchers are only local; raw GitHub `main` still has the stdin `BASH_SOURCE` defect.

## Environmental incident

Windows `bsdtar` 3.8.8 crashed while producing the portable archive and left a zero-byte file. The exact file was replaced with the .NET ZIP implementation, then all 419 extracted hashes, 98 critical files, and 20 sampled reads were verified. This did not alter the source vault or immutable final archive.
