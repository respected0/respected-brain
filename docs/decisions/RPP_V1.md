# RPP v1.0 - Respected SecondBrain server side

Status: implemented (Workstream B). Code: `src/respectedbrain/rpp.py`, entry
point `python -m respectedbrain rpp`. Tests: `tests/test_rpp.py`.

## What it is

The Respected Product Protocol (RPP) v1.0 is the minimal shared contract for the
three Respected products. It is **not** MCP and **not** a daemon: one JSON
request on stdin, one JSON response line on stdout of a private, hidden
subcommand with no public CLI and no network listener.

## Data root

The module accepts an explicit data/config root override so tests never touch
real user data:

- CLI: `python -m respectedbrain rpp --data-root <abs path>`
- Environment: `RESPECTED_RPP_DATA_ROOT=<abs path>`
- Otherwise the existing `respectedbrain.core.paths` resolution is used.

## Ops

`manifest`, `health`, `settings.schema`, `settings.validate`, `settings.apply`,
`settings.readback`. Unknown op -> `UNKNOWN_OP`; wrong protocol version ->
`PROTOCOL_UNSUPPORTED`; bad JSON/shape -> `BAD_REQUEST`. Responses always carry
`rpp`, `ok`, `operation_id`, `result`, `error`; no code path raises or prints a
traceback.

## Capabilities (real, pointable features only)

`capture` (memory.flush), `recall` (search.engine), `mcp_serve`
(integrations.mcp), `hooks_dispatch` (integrations.hooks), `briefing`
(briefing.service).

## Settings

The schema is an allow-list derived from keys that really exist in
`resources/defaults.json`: `summary_provider`, `provider_fallback`,
`integrations.global`, `integrations.mcp`, `integrations.schedule`,
`integrations.shortcut`. Validation runs the schema checks and then the existing
`core.config.validate_config`. `settings.apply` writes through the existing
`ConfigStore` (atomic temp file + replace) so the real config file is what
changes, and records a durable receipt under `<data root>/receipts/`.

Apply is idempotent per `operation_id`: replaying the same id with the same
settings returns the stored receipt unchanged; reusing an id with different
settings returns `OPERATION_ID_CONFLICT`. Invalid settings write nothing.
Receipts store only metadata (operation id, op, status, time, settings digest),
never setting values; `readback` masks `secret` fields.