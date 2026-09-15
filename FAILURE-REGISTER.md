# Failure Register

## Fixed and regression-tested

The first eight product fixes are in commit `7762df945109cc8d7921a2865f5bad81d01aa43b`; the reinstall repair is in `9625a3a8f6043379b28625e425c019ffd1b63663`. All fixes listed here were fast-forwarded to `origin/main`.

1. **Codex notify chain destruction.** Normal uninstall deleted an outer computer-use notifier when Respected appeared as nested `--previous-notify` JSON without a chain file. Added a RED regression, implemented nested-argv surgery, then GREEN; unrelated TOML bytes stayed exact.
2. **Wrong shortcut cleanup name.** `uninstall.py main()` ignored `--vault-path` when choosing the shortcut name. Added RED/GREEN regression and passed two live uninstall runs.
3. **Wrong upstream repository.** Six launchers cloned `respected0/secondbrain` and used `secondbrain-main`. Behavior tests captured the real argv RED; all now target `respected0/respectedbrain` and `respectedbrain-main`, GREEN on Windows and WSL.
4. **Windows pipe-to-IEX failure.** Parameter `ValidateSet` rejected an existing empty `$Environment` variable before the script ran. Exact IEX regression was RED; manual post-binding validation is GREEN.
5. **POSIX piped `BASH_SOURCE` failure.** `curl | bash` referenced unset `BASH_SOURCE[0]`, then could use an unrelated current-directory installer. Exact stdin regression was RED; all three shell launchers now handle stdin mode and force download, GREEN.
6. **Current scheduler tasks survived uninstall.** The uninstaller searched only obsolete display strings and depended on localized LIST output. A CSV/no-header prefix regression was RED; current and legacy managed prefixes are now deleted independent of locale, unrelated tasks are retained, and the live residual count is zero.
7. **BOOTSTRAP reinstall was not idempotent.** A second run used `copytree(..., dirs_exist_ok=False)` and raised `FileExistsError`. A RED regression now installs twice while hashing a user file; recognized vaults route through the safe updater, unknown non-empty targets still fail closed, and the test is GREEN on Windows and WSL.
8. **Purge could report false success.** `shutil.rmtree(..., ignore_errors=True)` could leave a vault behind and still print that it was deleted. A RED no-op-removal regression now requires a nonzero exit and explicit error while the target exists; permission recovery and post-delete existence verification are GREEN. The exact live disposable purge was rerun and removed the residual tree.
9. **Existing-vault reinstall skipped requested integrations and swallowed their failures.** The recognized-vault branch returned immediately after update/render, so removed global hooks, MCP, schedule, or shortcut state was not repaired. A real hybrid cycle reproduced the missing repair. Two RED regressions proved the skipped shortcut and lost global exit code. Optional integrations now share one fail-closed path for fresh and existing vaults; both tests are GREEN, deliberate hook/shortcut deletion was repaired, a failing global installer preserved exit code 9, and Windows plus WSL 377-test packages passed.
10. **Remote launcher staging leaked.** Successful Windows `install.ps1` runs left four exact `respected-brain-install-*` clone directories; all three POSIX launchers bypassed their `EXIT` trap by using `exec`. RED behavior tests reproduced both. Commit `6cdf3a6` adds PowerShell `finally` cleanup and lets POSIX traps run. Windows and WSL tests are GREEN, published install/update/uninstall runs left zero new staging directories, and the four old exact clones were removed.
11. **Repeated same-version update falsely failed.** `scripts/update_respected.py` intentionally returned `3` for an unchanged vault, but `update.py` reported rollback/failure and propagated `3`. The RED wrapper regression now maps only that documented no-op to success; commit `b835c19` returns `0` with an explicit already-current message. The final 378-test package and published Windows/WSL/hybrid double-update cycles passed.

## Unresolved release failures

None reproducible in the exercised product paths. Remaining acceptance items are environmental/account blockers listed in `RESIDUAL-RISKS.md`, not product failures.

## Environmental incident

Windows `bsdtar` 3.8.8 crashed while producing the portable archive and left a zero-byte file. The exact file was replaced with the .NET ZIP implementation, then all 419 extracted hashes, 98 critical files, and 20 sampled reads were verified. This did not alter the source vault or immutable final archive.
