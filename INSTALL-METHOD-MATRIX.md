# Installation Method Matrix

| Platform | AI-native / BOOTSTRAP | Published one-liner | Local repo + CLI | Evidence |
|---|---|---|---|---|
| Windows Native | VERIFIED | FAILED | VERIFIED | [Bootstrap](qa-evidence/20260915T010137+0300/windows-native/bootstrap/adapter/result.md); [local CLI](qa-evidence/20260915T010137+0300/windows-native/local-cli/adapter/result.md) |
| Pure WSL2 | VERIFIED | FAILED | VERIFIED | [Bootstrap](qa-evidence/20260915T010137+0300/wsl/bootstrap/adapter/result.md); [local CLI](qa-evidence/20260915T010137+0300/wsl/local-cli/adapter/result.md) |
| Hybrid Windows + WSL | VERIFIED | NOT VERIFIED | NOT VERIFIED | [Bootstrap lifecycle and bridge](qa-evidence/20260915T010137+0300/hybrid/bootstrap/adapter/result.md) |
| True Linux VM | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Host unavailable |
| Physical macOS | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Host unavailable |

The canonical BOOTSTRAP route is now fail-closed on unknown non-empty targets and idempotent on recognized vaults. The local patched launcher contract is GREEN on Windows and WSL. The published raw scripts at source commit remain FAILED until the fixes are reviewed and pushed: Windows fails in pipe-to-`iex` parameter binding; POSIX fails because piped execution reads an unset `BASH_SOURCE[0]` and may resolve `install.py` from the caller's current directory.
