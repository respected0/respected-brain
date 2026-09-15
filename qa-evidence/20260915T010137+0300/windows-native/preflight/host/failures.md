# Preflight Failures

## PF-GLOBAL-HOOK-PYTHON — FAILED

The installed Codex, Claude, and Gemini managed hook commands reference `py.exe -3`, while `python`, `python3`, and `py` do not resolve on the Windows PATH. This is an observed configuration/executable mismatch. It is not fixed or promoted to an integration failure until the installed hook is executed under a controlled test.

## Baseline sandbox artifacts

The first aggregate run reported access denied for nested `Start-Process` and WSL execution. Focused reruns outside the sandbox both exited 0, so those two failures are classified as harness artifacts rather than product defects.

## Portable archive tool failure

Windows bsdtar 3.8.8 crashed with exit code `-1073741819` while creating ZIP and left a zero-byte artifact. The exact zero-byte file was replaced with a .NET `ZipFile` archive, which was extracted and verified 419/419 against the snapshot. This tool failure did not alter the live vault or snapshot.
