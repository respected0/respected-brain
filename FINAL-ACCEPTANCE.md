# Respected Brain v0.0.1 — Final Acceptance

Run: `20260915T010137+0300`  
Source: `b835c19` (published `origin/main`)
Branch: `codex/v001-release-acceptance`
Fix commit: `7762df945109cc8d7921a2865f5bad81d01aa43b`
Repair commit: `9625a3a8f6043379b28625e425c019ffd1b63663`
Launcher cleanup commit: `6cdf3a6`
Idempotent update commit: `b835c19`

## Decision

Release acceptance is **BLOCKED**, with zero currently reproducible product failures. Windows Native, pure WSL, and the hybrid bridge have passing physical-host adapter/lifecycle evidence; all three installation entry points now execute from published `main`. The remaining acceptance gaps require authenticated provider accounts and hardware that was not available: no supported provider completed the required signed-in three-turn test, and no true Linux VM or physical macOS host was connected.

## Executed gates

- Windows: the final 378-test Python package completed with 8 explicit platform-conditioned skips and no failures; physical lifecycle smoke, installer, launcher, scheduler, hybrid bridge, Bash hook, and upstream suites passed.
- Pure WSL: the 377-test Python package completed under `/home/furkan` on the Linux filesystem with 8 explicit platform-conditioned skips and no failures; lifecycle smoke and both Bash suites passed.
- AI-native/BOOTSTRAP: clean Windows and pure-WSL installs plus exact repeats passed; user bytes stayed unchanged and renderer drift was zero.
- Hybrid BOOTSTRAP: NTFS install, two updates, `/mnt/c` same-file hash, two isolated-profile uninstalls, and reinstall passed.
- Hybrid local CLI: project-only and global+project cycles covered MCP/schedule/shortcut off and on, a 07:43 schedule, single-provider and custom fallback modes, repair, uninstall, and reinstall.
- Windows disposable local CLI: Unicode/emoji/space path install, two updates, render check, and two uninstalls passed.
- Published one-liners: remote Windows Native, pure WSL-on-ext4, and Hybrid Windows+WSL installs passed from `raw.githubusercontent.com/.../main`; two same-version updates and two data-preserving uninstalls returned zero. POSIX Journal hash stayed byte-identical and all observed bootstrap temp clones were removed.
- Live uninstall: two runs passed; all 419 archived files remained byte-identical after uninstall and unrelated global configuration survived.
- Final live install: a clean canonical Windows-native bootstrap install plus idempotent repeat, exact persistent Python render, global integration, MCP registration, and `testOS.url` creation passed. Schedule remains intentionally off.

Automated adapter results are not real-provider acceptance. Eight platform-conditioned unit skips in each host run were not promoted to separate `VERIFIED` records.

## Data protection

The immutable snapshot contains 419 files and 27,465,689 bytes. Snapshot/source and extracted ZIP hashes matched for all 419 files; 98 critical files and 20 deterministic archive reads were checked. Before the user-authorized clean rebuild, normal uninstall preserved all 419 files and changed no human-authored region. The two observed non-manifest byte differences were one line inside the explicitly delimited managed briefing block in `Dashboard.md` and a Python `.pyc` cache file. The final clean vault intentionally does not auto-restore or mix those archived legacy notes.

Archive ZIP: `C:\Users\Furkan\Documents\Obsidian\testOS-QA-archives\20260915T010137+0300\testOS-portable.zip`  
SHA-256: `6cf621c2c731f158973e59d546d38db99c25e39f4a5ae0305ff82522187bb330`

## Final host state

- Vault: `C:\Users\Furkan\Documents\Obsidian\testOS`
- Profile: `windows-native`
- Python: `C:\Users\Furkan\AppData\Local\Python\pythoncore-3.14-64\python.exe`
- Global hooks: installed; prior Codex computer-use notify remains chained.
- MCP: `respected-vault` present in Gemini/Antigravity, Claude, and Cursor configurations; unrelated servers retained.
- Shortcut: `C:\Users\Furkan\Desktop\testOS.url`
- Managed scheduled tasks: zero.
- Push: verified commits were fast-forwarded to `origin/main`; published source tested at `b835c19`.

See [results.json](results.json), [platform/provider matrix](PLATFORM-PROVIDER-MATRIX.md), [installation matrix](INSTALL-METHOD-MATRIX.md), [feature matrix](FEATURE-MATRIX.md), and [failure register](FAILURE-REGISTER.md).
