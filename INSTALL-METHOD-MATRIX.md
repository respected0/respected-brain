# Installation Method Matrix

| Platform | AI-native / BOOTSTRAP | Published one-liner | Local repo + CLI | Evidence |
|---|---|---|---|---|
| Windows Native | VERIFIED | VERIFIED | VERIFIED | [Bootstrap](qa-evidence/20260915T010137+0300/windows-native/bootstrap/adapter/result.md); [published one-liner](qa-evidence/20260915T010137+0300/windows-native/one-liner/remote/result.md); [local CLI](qa-evidence/20260915T010137+0300/windows-native/local-cli/adapter/result.md) |
| Pure WSL2 | VERIFIED | VERIFIED | VERIFIED | [Bootstrap](qa-evidence/20260915T010137+0300/wsl/bootstrap/adapter/result.md); [published one-liner](qa-evidence/20260915T010137+0300/wsl/one-liner/remote/result.md); [local CLI](qa-evidence/20260915T010137+0300/wsl/local-cli/adapter/result.md) |
| Hybrid Windows + WSL | VERIFIED | VERIFIED | VERIFIED | [Bootstrap lifecycle and bridge](qa-evidence/20260915T010137+0300/hybrid/bootstrap/adapter/result.md); [published one-liner](qa-evidence/20260915T010137+0300/hybrid/one-liner/adapter/result.md); [local CLI matrix](qa-evidence/20260915T010137+0300/hybrid/local-cli/adapter/result.md) |
| True Linux VM | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Host unavailable |
| Physical macOS | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | Host unavailable |

The canonical BOOTSTRAP route is fail-closed on unknown non-empty targets and idempotent on recognized vaults. Published Windows and POSIX launchers were exercised from `main` after push. Their prior IEX/stdin failures are fixed, repeated updates are successful no-ops, and temporary remote-clone staging is cleaned on both platforms.
