# Platform / Provider Matrix

`VERIFIED` below is reserved for executed adapter/host gates. Real-provider rows remain blocked or unverified.

| Platform | Host/adapters | Codex | Claude | Cursor | Antigravity | Gemini | Acceptance |
|---|---|---|---|---|---|---|---|
| Windows Native | VERIFIED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | FAILED |
| Pure WSL2 (ext4) | VERIFIED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | FAILED |
| Windows + WSL bridge | VERIFIED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | FAILED |
| True Linux VM | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |
| Physical macOS | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED |

Windows Codex 0.154.0-alpha.6.2 was found, but the real-account call was rejected because it required explicit approval to use the signed-in account with untrusted project hooks. The other Windows and all WSL provider executables were absent. No Linux VM or macOS host was connected.

Adapter evidence: [Windows smoke](qa-evidence/20260915T010137+0300/windows-native/local-cli/adapter/smoke.json), [WSL smoke](qa-evidence/20260915T010137+0300/wsl/local-cli/adapter/smoke.json), [hybrid bootstrap](qa-evidence/20260915T010137+0300/hybrid/bootstrap/adapter/result.md).

## Main acceptance matrix

`Adapter` rows prove executed lifecycle behavior only. The grouped authenticated-provider rows cover Codex, Claude, Cursor, Antigravity, and Gemini; none is promoted from adapter evidence.

| Platform | Install method | Provider | Project/global | MCP | Schedule | Shortcut | Per-turn daily | Session upsert | Catch-up | Fallback | Update | Uninstall | Reinstall | Data protection | Final status | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Windows Native | BOOTSTRAP | Adapter | VERIFIED | VERIFIED | VERIFIED (off) | VERIFIED | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/windows-native/bootstrap/adapter/result.md) |
| Windows Native | Published one-liner | Adapter | VERIFIED (project) | VERIFIED (off) | VERIFIED (off) | VERIFIED (off) | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | VERIFIED (twice) | VERIFIED (twice) | NOT VERIFIED | VERIFIED | VERIFIED (launcher lifecycle) | [evidence](qa-evidence/20260915T010137+0300/windows-native/one-liner/remote/result.md) |
| Windows Native | Local repo + CLI | Adapter | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/windows-native/local-cli/adapter/result.md) |
| Pure WSL | BOOTSTRAP | Adapter | VERIFIED (project) | VERIFIED (off) | VERIFIED (off) | NOT SUPPORTED (`.url`) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED (suite) | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/wsl/bootstrap/adapter/result.md) |
| Pure WSL | Published one-liner | Adapter | VERIFIED (project) | VERIFIED (off) | VERIFIED (off) | VERIFIED (off) | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | VERIFIED (twice) | VERIFIED (twice) | NOT VERIFIED | VERIFIED (Journal hash) | VERIFIED (launcher lifecycle) | [evidence](qa-evidence/20260915T010137+0300/wsl/one-liner/remote/result.md) |
| Pure WSL | Local repo + CLI | Adapter | VERIFIED | VERIFIED (contract) | VERIFIED (contract) | VERIFIED (`.desktop` contract) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/wsl/local-cli/adapter/result.md) |
| Hybrid Windows + WSL | BOOTSTRAP | Adapter | VERIFIED (project) | VERIFIED (off) | VERIFIED (off) | VERIFIED (off) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/hybrid/bootstrap/adapter/result.md) |
| Hybrid Windows + WSL | Published one-liner | Adapter | VERIFIED (project) | VERIFIED (off) | VERIFIED (off) | VERIFIED (off) | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | VERIFIED (twice) | VERIFIED (twice) | NOT VERIFIED | VERIFIED (vault retained) | VERIFIED (launcher lifecycle) | [evidence](qa-evidence/20260915T010137+0300/hybrid/one-liner/adapter/result.md) |
| Hybrid Windows + WSL | Local repo + CLI | Adapter | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED (synthetic) | VERIFIED | VERIFIED | VERIFIED | VERIFIED | VERIFIED | [evidence](qa-evidence/20260915T010137+0300/hybrid/local-cli/adapter/result.md) |
| Windows Native | Any | Codex/Claude/Cursor/Antigravity/Gemini authenticated | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | [provider status](PLATFORM-PROVIDER-MATRIX.md) |
| Pure WSL | Any | Codex/Claude/Cursor/Antigravity/Gemini authenticated | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | [provider status](PLATFORM-PROVIDER-MATRIX.md) |
| Hybrid Windows + WSL | Any | Codex/Claude/Cursor/Antigravity/Gemini authenticated | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | BLOCKED | [provider status](PLATFORM-PROVIDER-MATRIX.md) |
| True Linux VM | All three | All supported | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | [residual risks](RESIDUAL-RISKS.md) |
| Physical macOS | All three | All supported | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | NOT VERIFIED | [residual risks](RESIDUAL-RISKS.md) |
