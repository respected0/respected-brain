# Legacy Usage Analysis — 2026-10-11

## Result

- **No candidate meets the REMOVE-SAFE bar** under the accessible in-repo evidence and worktree boundary.
- **Modules with current callers, tests, packaged resources, CLI/docs contracts, or installer/shortcut contracts are active product surfaces**, not safe-to-delete remnants. The only unreferenced shim remains **KEEP** because its programmatic-entry contract is unverified.
- **`src/respectedbrain/rpp.py` does not exist** in this worktree.
- No in-repo references to `SecondBrain`, `respected-orchestrator`, or `respected-hub` were found.

## Scope and limits

- Analysis was read-only; no source, test, packaging, map, or inventory files were changed.
- Sibling repositories and parent project directories were **not accessed**, per the worktree boundary. Therefore no claim is made about whether `../respected-orchestrator` or `../respected-hub` contains a newer superset.
- Any verdict that would depend on an unverified sibling or parent contract is marked **KEEP**.
- No tests or acceptance commands were run in this sandbox.

## Candidate inventory

| Path | Lines | Verdict |
| --- | ---: | --- |
| `src/respectedbrain/orchestration/runner.py` | 464 | KEEP |
| `src/respectedbrain/orchestration/antigravity_orchestrator.py` | 1175 | KEEP |
| `src/respectedbrain/orchestration/orchestrate.py` | 4 | KEEP |
| `src/respectedbrain/gateway/server.py` | 496 | KEEP |
| `src/respectedbrain/cli.py` | 436 | KEEP |
| `src/respectedbrain/briefing/service.py` | 290 | KEEP |
| `src/respectedbrain/integrations/backend.py` | 502 | KEEP |
| `src/respectedbrain/integrations/rendering.py` | 443 | KEEP |
| `src/respectedbrain/maintenance/vault_linter.py` | 285 | KEEP |
| `src/respectedbrain/memory/graph/graph_analysis.py` | 430 | KEEP |
| `src/respectedbrain/rpp.py` | absent | N/A |

## Evidence

### `src/respectedbrain/orchestration/runner.py` — KEEP

- **Callers**
  - `src/respectedbrain/cli.py:105` registers `orchestrate`.
  - `src/respectedbrain/cli.py:398` imports and calls `runner.run`.
  - `src/respectedbrain/gateway/server.py:31` imports `runner`.
  - `src/respectedbrain/gateway/server.py:247`, `:326`, `:337`, and `:343` call `list_runs`, `start_run`, `apply_run`, and `reject_run`.
- **Tests**
  - `tests/foundation_maintenance_orchestration_test.py:46`, `:67`, `:81`, `:140`, and `:159` cover project isolation, selected-vault boundaries, Antigravity failure recording, and gateway service contracts.
  - `tests/orchestration_review_test.py:13` imports `runner`.
  - `tests/entry_review_test.py:119` covers malformed run evidence.
- **Contracts**
  - `docs/development/CLI.md:114` documents `orchestrate`.
  - `src/respectedbrain/resources/skills/kod-orkestrasyon/SKILL.md:24`, `:27`, and `:30` give native CLI examples.
  - `pyproject.toml:16` exposes the single `respectedbrain` entry point that reaches this code through `cli.py`.
- **Side effects**
  - Creates `DataRoot/state/orchestration`.
  - Creates `.worktrees` under the explicit code project.
  - Runs Git and worker CLI subprocesses.
  - Can apply patches and remove run records.
  - Does not intentionally write to VaultRoot or AppRoot.
- **Verdict rationale:** active CLI, dashboard API, tests, packaged skill, and docs all depend on it.

### `src/respectedbrain/orchestration/antigravity_orchestrator.py` — KEEP

- **Callers**
  - `src/respectedbrain/orchestration/runner.py:311` dispatches `antigravity` subcommands to this module.
  - Direct test imports exist in `tests/antigravity_orchestrator_test.py:21`.
- **Tests**
  - `tests/antigravity_orchestrator_test.py:111` through `:769` cover policy, worker resolution, lane isolation, scope enforcement, acceptance, patch export, and apply safety.
  - `tests/orchestration_recovery_test.py:12` imports the test helper for this module.
- **Contracts**
  - No public CLI docs advertise the internal `antigravity` subcommand, but `runner.py` exposes it and tests exercise it.
- **Side effects**
  - Creates a worktree lane and run state under `DataRoot/state/orchestration`.
  - Creates a writer lock, logs, patch, and verification evidence.
  - Runs worker and acceptance subprocesses inside the isolated worktree.
  - Does not intentionally write to VaultRoot or AppRoot.
- **Verdict rationale:** although it is not documented as a public command, it is actively dispatched and strongly tested. Without the forbidden sibling comparison, removal is uncertain; therefore **KEEP**.

### `src/respectedbrain/orchestration/orchestrate.py` — KEEP

- **Callers**
  - No source, test, packaging, non-generated docs, resource, hook, MCP, or scheduler reference was found. The generated repository atlas references the path, but the later map-sync phase owns that update.
  - `src/respectedbrain/cli.py:398` imports `runner.run` directly, bypassing this shim.
- **Tests**
  - No test imports or executes this module.
- **Contracts**
  - `pyproject.toml:16` defines only `respectedbrain.cli:main`; this file is not an entry point.
  - No packaged resource or documented command references it.
- **Side effects**
  - None; it only re-exports `runner.run`.
- **Verdict rationale:** it has no in-repo caller, test, entry point, or documented CLI contract, but its docstring explicitly calls it a programmatic entry and the external Python/sibling contract could not be inspected. Under the uncertainty rule, it remains **KEEP**.

### `src/respectedbrain/gateway/server.py` — KEEP

- **Callers**
  - `src/respectedbrain/cli.py:389` calls `start_server` for `dashboard`.
- **Tests**
  - `tests/foundation_services_test.py:12` imports `create_server`.
  - `tests/foundation_services_test.py:18`, `:27`, `:51`, `:57`, `:97`, `:110`, `:121`, `:126`, `:137`, and `:144` exercise local API boundaries, capture, search, config, and static UI behavior.
- **Contracts**
  - `docs/development/CLI.md:89` documents `dashboard`.
  - `docs/guides/DAILY_USE.md:43` documents the local control panel.
  - `src/respectedbrain/resources/skills/kod-orkestrasyon/SKILL.md:34` points users to the dashboard.
  - `pyproject.toml:26` packages `gateway/web/index.html`.
- **Side effects**
  - Serves a loopback HTTP dashboard.
  - Reads config, vault notes, and state.
  - Can create quick-capture notes, reindex search, run briefing/compile, and start/apply/reject orchestration runs.
- **Verdict rationale:** this is an active local product surface with CLI, resource, docs, and tests. Removing it would break capture, search, briefing, compile, and orchestration UI access.

### `src/respectedbrain/cli.py` — KEEP

- **Callers**
  - `pyproject.toml:17` makes `respectedbrain.cli:main` the only package entry point.
  - `packaging/entrypoint.py:1` imports `cli.main`.
- **Tests**
  - `tests/runtime_layout_test.py:16` verifies public command dispatch.
  - `tests/foundation_packaged_commands_test.py:47` verifies `orchestrate` CLI flags and selected UUID.
- **Contracts**
  - `docs/development/CLI.md:89` and `:114` document `dashboard` and `orchestrate`.
- **Side effects**
  - Dispatches all product commands, including dashboard and orchestration.
- **Verdict rationale:** primary composition and entry point.

### `src/respectedbrain/briefing/service.py` — KEEP

- **Callers**
  - `src/respectedbrain/cli.py:383` calls `run_if_due`.
  - `src/respectedbrain/gateway/server.py:351` calls `run_if_due`.
- **Tests**
  - `tests/morning_briefing_test.py:102`, `:170`, `:198`, `:262`, `:265`, `:311`, and `:329` cover dashboard preservation, legacy marker migration, concurrency, and failure safety.
- **Contracts**
  - Scheduled briefing is a protected memory job.
  - `src/respectedbrain/integrations/scheduling/service.py:58` launches the `briefing` command.
- **Side effects**
  - Updates the managed block in `🎯 100-Command-Center/Dashboard.md`.
  - Writes briefing notes and state/cache.
- **Verdict rationale:** the term “dashboard” here means the **vault note**, not the HTTP gateway. This is an active briefing contract and must be protected.

### `src/respectedbrain/integrations/backend.py` — KEEP

- **Callers**
  - Installer and integration flows use this backend for transactional writes.
- **Tests**
  - `tests/foundation_integrations_test.py:514` covers legacy rollback and ownership.
- **Contracts**
  - `src/respectedbrain/integrations/backend.py:467` verifies a legacy scheduled task.
  - `src/respectedbrain/integrations/backend.py:477` verifies a legacy `dashboard.py` shortcut before ownership.
- **Side effects**
  - Transactional integration ownership and rollback records.
- **Verdict rationale:** references to `dashboard.py` are **legacy migration/installer safety**, not dead dashboard logic.

### `src/respectedbrain/integrations/rendering.py` — KEEP

- **Callers**
  - Integration planner and installer shortcut flow.
- **Tests**
  - `tests/foundation_integrations_test.py:512` asserts the native shortcut arguments are `dashboard --vault-id <UUID>`.
  - `tests/wizard_test.py:64` covers requested dashboard shortcut rendering.
- **Contracts**
  - `src/respectedbrain/integrations/rendering.py:410` constructs the native dashboard shortcut.
- **Side effects**
  - Plans a Windows desktop shortcut.
- **Verdict rationale:** active installer and native shortcut contract.

### `src/respectedbrain/maintenance/vault_linter.py` — KEEP

- **Callers**
  - `src/respectedbrain/maintenance/__init__.py` dispatches maintenance tools.
- **Tests**
  - `tests/foundation_maintenance_orchestration_test.py:36` and `:50` exercise the selected vault boundary.
  - `tests/vault_hygiene_test.py:157` covers dead links and orphans.
- **Contracts**
  - `src/respectedbrain/maintenance/vault_linter.py:61` ignores `dashboard` as an orphan basename.
- **Side effects**
  - Reads and optionally repairs vault notes.
- **Verdict rationale:** this is vault-note metadata, not HTTP dashboard orchestration.

### `src/respectedbrain/memory/graph/graph_analysis.py` — KEEP

- **Callers**
  - Memory graph and recall/search workflows.
- **Tests**
  - Memory graph and session tests exercise this module.
- **Contracts**
  - `src/respectedbrain/memory/graph/graph_analysis.py:29` skips root `Dashboard.md` when analyzing the vault graph.
- **Side effects**
  - Reads vault Markdown to build graph/index data.
- **Verdict rationale:** protected memory/graph behavior; `Dashboard.md` is a vault note name.

### `src/respectedbrain/rpp.py` — N/A

- No such file exists in this worktree.
- No references to `rpp.py`, `respectedbrain.rpp`, or `import rpp` were found.

## Other references

- **Packaging**
  - `pyproject.toml:16` defines the sole `respectedbrain` entry point.
  - `pyproject.toml:26` packages `gateway/web/index.html`.
  - `pyproject.toml:48` packages `skills/kod-orkestrasyon/SKILL.md`.
  - `packaging/entrypoint.py:1` imports `cli.main`.
- **Docs**
  - `docs/development/CLI.md:89` and `:114` document `dashboard` and `orchestrate`.
  - `docs/guides/DAILY_USE.md:43` documents the local dashboard.
  - `docs/guides/DAILY_USE.md:51` documents orchestration boundaries.
  - `docs/decisions/MODULAR_FOUNDATION.md:257` and `:258` define gateway and orchestration as approved modules.
- **Resources**
  - `src/respectedbrain/resources/skills/kod-orkestrasyon/SKILL.md:24`–`:35` documents native orchestration and dashboard usage.
  - `src/respectedbrain/resources/gateway/web/index.html:958`, `:1225`, `:1242`, and `:1269` call the orchestration API.
- **Hooks / MCP / scheduling**
  - No orchestration or gateway imports were found.
  - `src/respectedbrain/integrations/hooks/bridge.py:307` remains the hook dispatcher.
  - `src/respectedbrain/integrations/mcp/server.py:423` remains the MCP stdio entry.
  - `src/respectedbrain/integrations/scheduling/service.py:58` schedules `briefing`.
  - These contracts are protected and should not be changed by an orchestration cleanup.

## Protected contracts

Do not remove or weaken:

- capture/recall/search/embeddings
- memory compiler and briefing
- hooks and provider bridges
- MCP server
- vault and scheduled memory jobs
- backup and installer contracts
- native launcher, shortcut, and rollback ownership

## Removal manifest

No file is recommended for removal in this worktree.

If the external programmatic-entry contract is later confirmed absent, `src/respectedbrain/orchestration/orchestrate.py` (4 lines) is the first and only candidate to reassess.

## Required checks for a future removal

Before removal:

- `tests/foundation_packaged_commands_test.py`
- `tests/runtime_layout_test.py`
- `tests/foundation_maintenance_orchestration_test.py`
- `tests/orchestration_review_test.py`
- `tests/orchestration_recovery_test.py`
- `tests/antigravity_orchestrator_test.py`
- `tests/foundation_services_test.py`
- `tests/entry_review_test.py`

After removal:

- Repeat the focused checks above.
- Run the full suite used by the product gate.
- Run `python tools/repository_map.py --update`.
- If that reassessed removal is applied, run `python tools/repository_map.py --accept-reviewed src/respectedbrain/orchestration/orchestrate.py`.
- Run `python tools/repository_map.py --write`.
- Run `python tools/repository_map.py --check`.

## Rollback

- No rollback is needed because no removal is planned.
- If a later phase removes `src/respectedbrain/orchestration/orchestrate.py`, revert that removal commit.
- Re-run the focused checks listed above.
- Regenerate and validate the repository map.
- No data rollback would be needed because the reassessed shim has no runtime side effects.




