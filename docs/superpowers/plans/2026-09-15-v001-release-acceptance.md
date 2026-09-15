# Respected Brain v0.0.1 Release Acceptance Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce evidence-backed release acceptance for Respected Brain v0.0.1 across Windows Native, pure WSL, hybrid Windows+WSL, pure Linux VM, and physical macOS without treating simulation or configuration inspection as real-host success.

**Architecture:** Run all destructive lifecycle work only against validated disposable vaults and isolated HOME/profile roots. Keep the live `testOS` backup immutable, store redacted evidence below one run ID, fix reproducible product defects with strict RED/GREEN regression tests, and classify unavailable physical hosts or authenticated agents honestly.

**Tech Stack:** Python 3 standard library, PowerShell 7, Windows PowerShell-compatible scripts, POSIX shell, WSL2 Ubuntu, unittest, JSON, Markdown, Git.

**Spec:** `docs/superpowers/specs/2026-09-14-v0.0.1-golden-hardening-design.md` plus the user-approved 2026-09-15 release-acceptance contract in this task.

## Global Constraints

- Source truth is this repository; `C:\Users\Furkan\Documents\Obsidian\testOS` is live user data, not source code.
- Never use `--purge-vault` against the live vault.
- Evidence must not contain prompts, transcripts, note bodies, credentials, cookies, API keys, or tokens.
- Only executed behavior can be `VERIFIED`; unavailable authenticated agents are `BLOCKED`, and unavailable physical hosts are `NOT VERIFIED`.
- Every product fix requires a focused failing regression test, observed RED, minimal implementation, observed GREEN, platform package rerun, and full regression rerun.
- Do not push or merge without explicit user authority.

---

### Task 1: Freeze preflight and backup evidence

**Files:**
- Create: `qa-evidence/20260915T010137+0300/windows-native/preflight/host/environment.json`
- Create: sibling `commands.json`, `checks.json`, `timings.json`, `hashes-before.json`, `hashes-after.json`, `failures.md`, and `result.md`

**Interfaces:**
- Consumes: read-only host inventory and external backup verification metadata.
- Produces: a redacted baseline that later lifecycle tests can compare against.

- [ ] Record OS/build, architecture, shell, every Python resolution result, Git, WSL, filesystem, repository state, agent executables, Obsidian, live-vault path safety, global config paths, schedulers, and MCP registration names.
- [ ] Reference the immutable snapshot and ZIP verification without copying private file contents into the repository.
- [ ] Validate both backup forms against the same 419-file manifest and verify the critical paths and 20 deterministic archive reads.

### Task 2: Characterize and remove the current managed installation

**Files:**
- Create: `qa-evidence/20260915T010137+0300/windows-native/existing-install/lifecycle/*`
- Modify only if a confirmed defect exists: `uninstall.py` and its focused tests.

**Interfaces:**
- Consumes: preflight semantic fingerprints of global configs and live-vault hashes.
- Produces: data-preserving uninstall result, second-run idempotency result, and preserved unrelated-config proof.

- [ ] Read the uninstaller completely and run `--help` before mutation.
- [ ] Store private safety copies outside `qa-evidence`; evidence retains only SHA-256 and redacted semantic fingerprints.
- [ ] Run normal uninstall twice with the bundled QA interpreter and assert live-vault file hashes are unchanged except for explicitly documented asynchronous session files.
- [ ] Verify managed hooks/MCP/scheduler/shortcut removal and unrelated config preservation.

### Task 3: Execute Windows Native installation-method cycles

**Files:**
- Create evidence below `qa-evidence/20260915T010137+0300/windows-native/{bootstrap,one-liner,local-cli}/...`
- Modify product/test files only through defect-specific TDD cycles.

**Interfaces:**
- Consumes: isolated Windows HOME roots and disposable Unicode/space-containing vaults.
- Produces: install/update/update/uninstall/uninstall/reinstall results for every supported option group.

- [ ] Prove clean start, execute each method, verify components and exit behavior, update twice, hash user-owned files, uninstall twice, and prove clean separation before the next method.
- [ ] Exercise project-only, global-only, combined, MCP on/off, scheduler on/off/custom time, shortcut on/off, provider order/lock, and Windows-native profile cases.
- [ ] Exercise missing Python, Microsoft Store alias, download failure, interrupted staging, rollback, unsafe paths, read-only targets, missing Desktop, existing shortcut, and competing installers.

### Task 4: Execute pure WSL and hybrid cycles

**Files:**
- Create evidence below the run ID for `wsl` and `windows-wsl`.
- Modify product/test files only through defect-specific TDD cycles.

**Interfaces:**
- Pure WSL uses repo, HOME, and vault under ext4 `/home/furkan`.
- Hybrid uses a Windows NTFS vault and its exact `/mnt/c/...` mapping.

- [ ] Run all three installation methods in clean disposable roots for each profile.
- [ ] Verify POSIX-only pure WSL behavior, Linux Python, systemd/explicit fallback, path conversion, `wsl.exe --cd`, shared-daily visibility, and simultaneous Windows/WSL writes.
- [ ] Run lifecycle, concurrency, crash-recovery, fallback, data-preservation, and injection suites without granting `VERIFIED` to authenticated-provider tests that were not executed.

### Task 5: Package and classify unavailable real hosts and agents

**Files:**
- Create evidence/result records for `linux-vm` and `macos-physical`.
- Update: `RESIDUAL-RISKS.md` and the platform/provider matrix.

**Interfaces:**
- Consumes: callable physical hosts and authenticated agent sessions, if present.
- Produces: real evidence or explicit `BLOCKED`/`NOT VERIFIED` records.

- [ ] Detect whether a true non-WSL Linux VM and physical macOS host are accessible; do not substitute Docker, WSL, or `macos-latest` CI.
- [ ] Detect each real authenticated provider CLI/app separately on every host.
- [ ] For unavailable prerequisites, record the exact missing access and ready-to-run command bundle rather than inferred success.

### Task 6: Run provider turn, memory-transfer, fallback, and adversarial suites

**Files:**
- Create per-provider evidence under every accessible platform/method.
- Modify focused production/tests only after observed failures.

**Interfaces:**
- Consumes: real authenticated providers where available; disposable synthetic fixtures elsewhere.
- Produces: distinct real-session status and adapter-contract status.

- [ ] Send the three approved QA turns in one real session per provider and inspect the daily file after each response for bounded latency, single-block upsert, marker safety, human-line preservation, and transcript secrecy.
- [ ] Exercise session-end, pre-compact, restart, catch-up, duplicate delivery, cross-provider memory transfer, fallback failure/recovery, 20 sessions, 24 processes, out-of-order revisions, crash points, date/clock boundaries, and secret/injection handling.
- [ ] Never promote an adapter test to real-agent `VERIFIED`.

### Task 7: Produce final matrices and clean-state proof

**Files:**
- Create: `FINAL-ACCEPTANCE.md`, `PLATFORM-PROVIDER-MATRIX.md`, `INSTALL-METHOD-MATRIX.md`, `FEATURE-MATRIX.md`, `FAILURE-REGISTER.md`, `RESIDUAL-RISKS.md`, `RESTORE-TESTOS.md`, and `results.json`.

**Interfaces:**
- Consumes: every check record under the run ID.
- Produces: human and machine-readable totals, evidence links, final installation path, backup hash, residual risks, and Git state.

- [ ] Validate schema and status vocabulary, reconcile counts from `results.json`, verify every matrix row links to evidence, and ensure no secret-like content exists in evidence.
- [ ] Remove only validated disposable roots and temporary integrations; leave the backup immutable and no test stubs, schedulers, MCP entries, shortcuts, or hooks behind.
- [ ] Run the full fresh regression package plus `git diff --check`, report branch/dirty state, and stop before push/merge.
