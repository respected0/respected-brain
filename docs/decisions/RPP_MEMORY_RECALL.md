# RPP v1.1 `memory.recall` (read-only memory access for other products)

Status: implemented 2026-10-15 (first project executed through Orchestrator). Not exposed by the Hub yet.

## Contract
Three ops, protocol 1.1 only (a 1.0 request gets `UNSUPPORTED_OP`; the 1.0 manifest does not list the `memory_recall` capability):

| op | payload | result |
|---|---|---|
| `memory.grant` (needs `operation_id`, which becomes the grant id) | `{label, max_results?}` | `{grant_id, token, label, vault_id, max_results, created_at}`; the token is shown once |
| `memory.revoke` | `{grant_id}` | `{grant_id, revoked}` (idempotent) |
| `memory.recall` | `{token, query, limit?, snippet_chars?, category?}` | `{results[{path,title,category,tags,snippet,score}], count, dropped, limit, read_only, index{state,...}, vault_id, grant_id}` |

## Safety rules (each has a test)
- **Authorization is a secret, not a name.** A grant token created by whoever may run `settings.apply` on this data root is required;
  only its sha256 is stored (`memory-grants.json`, data root). A caller-supplied host or consumer name is rejected, never trusted.
  Wrong, missing and revoked tokens give the same `PERMISSION_DENIED` message. At most 20 active grants.
- **Vault boundary.** The vault is always the registered active vault; `vault_path`, `path`, `root`, `host` etc. are `BAD_REQUEST`.
  A grant is bound to the vault id it was created for and is denied after the active vault changes.
- **Read-only.** `SearchEngine.open_read_only` opens the index with SQLite `mode=ro` + `query_only`, takes no writer lease, creates no
  directory or file and never builds or repairs the index. Tests compare a vault + data root snapshot (path, size, mtime, sha256) before/after.
- **Missing / outdated index.** Missing: `INDEX_MISSING`; unusable: `INDEX_INVALID` (hint: refresh it with the SecondBrain product).
  Outdated: `index.state` = `stale` (mtime comparison, bounded to 5000 files, `unknown` beyond). **A hit is only returned if the file's current sha256 equals the one
  recorded at indexing time** (confirmed leak before 2026-10-15: text removed from a note after indexing was still returned from the old index). Hits whose file vanished are
  counted in `dropped`, hits whose file changed in `dropped_stale`; the result can therefore be shorter than `limit`. A change between the hash check and the reply is not
  detectable without locking.
- **Limits.** Query 1-200 chars and 1-12 word terms; `limit` 1-20 (also clamped to the grant); `snippet_chars` 40-400; title 200,
  category 64, tags 200 characters; control characters and highlight markers removed; paths must be relative, normal and inside the vault.
  File bodies are never returned.

## Known limits
- The grant op is as privileged as `settings.apply` (anyone who can run the RPP process on this data root can mint a token). The Hub does not
  yet offer a UI or an allow-listed IPC route for grants; until it does, only direct RPP callers can use them.
- `index_state` walks the vault (stat only); on very large vaults it reports `unknown`.
- No audit log of recalls (kept out on purpose: recall writes nothing).
- Orchestrator does not call `memory.recall` yet.
- Repository inventory (`docs/repository_inventory.json`) was already stale for the RPP files; the new files are not described there yet.

## Index refresh (`memory.index.status`, `memory.index.refresh`) — added 2026-10-15
`memory.recall` stays read-only and never builds or repairs the index. Making the index current is a separate, explicitly authorized operation (protocol 1.1, capability `memory_index`):

| op | payload | result |
|---|---|---|
| `memory.index.status` | none | `{vault_id, index:{state: missing|invalid|fresh|stale|unknown, indexed_files, checked_files, changed_files}, last_refresh|null}`; no side effects |
| `memory.index.refresh` (needs `operation_id`) | exactly `{confirm: true, force?: bool}` | `{vault_id, indexed, skipped, deleted, total, duration_seconds, force, replayed, index}` |

- Authorization: the explicit `confirm: true` plus an operation id; any other key (path, vault, host) is `BAD_REQUEST`. It acts on the active registered vault only. The Hub is the intended caller
  (the user's click is the authorization); the Orchestrator's recall grant does not allow it, and the Hub's webview bridge cannot call it.
- Reuse: `SearchEngine.index_vault` (incremental by sha256; `force` re-indexes everything) under the existing writer lease; `INDEX_BUSY` when another writer holds it. Nothing inside the vault is written.
  The only writes are the engine's own index in the data root's cache folder, `memory-index-refresh.json` and `memory-index-operations/<id>.json` (newest 50 kept).
- Idempotent: replaying an operation id with the same payload returns the stored result (`replayed: true`) without re-indexing; the same id with another payload is `OPERATION_ID_CONFLICT`.
- Limits: the refresh runs synchronously, so a very large vault can take minutes (the Hub allows 15); there is no progress reporting or cancellation yet.

## Authorized memory writes (`memory.write`, `memory.write.revert`) — added 2026-10-15
Capability `memory_write` (protocol 1.1 only; hidden from 1.0 manifests). A grant carries `write: true|false` (default false; created by `memory.grant {label, write?}`); a read-only token is `PERMISSION_DENIED` for writes.

| op | payload | result |
|---|---|---|
| `memory.write` (needs `operation_id`) | `{token, title(1-120), body(1-20000), tags?(<=8)}` | `{path, sha256, grant_id, created_at, replayed, indexed}` |
| `memory.write.revert` | `{token, operation_id}` | `{operation_id, reverted, already_gone}` |

Safety (tests `tests/test_rpp_memory_write.py`): the note is a NEW file in the fixed folder `🔮 850-Companion/Inbox/Orchestrator/` of the active vault (never an existing file, never a caller path/vault: any other key is `BAD_REQUEST`);
created under the writer lease via temp file + atomic replace; front matter records `source: orchestrator`, grant id, operation id; at most 500 notes; idempotent per operation id (same payload replays, other payload `OPERATION_ID_CONFLICT`);
revert deletes only a note this grant wrote and only while its sha256 is unchanged (`NOTE_CHANGED` otherwise). After a write the index is refreshed incrementally (best effort) so the note is recallable.
Consumers: Hub `memory_access_enable(write)` (separate checkbox, off by default) creates the grant and sets Orchestrator `memory_write`; Orchestrator MCP tool `orchestrator_memory_note` (reusable knowledge only, not task history; `disabled` unless both permissions exist).

## Automatic index freshness (no Hub, no daemon) — added 2026-10-15
`recall` stays strictly read-only and hash-verified. The index is refreshed incrementally (`search/freshness.py::refresh_now`, sha256 based, writer lease, `INDEX_BUSY` -> retry) by the product's own processes:
CLI `respectedbrain index-refresh --vault-id`, the detached `flush --maybe-compile` child launched at every AI-client session start, the end of every `flush`, the scheduled morning-briefing task, and after every `memory.write`.
Limit: a vault edited outside any AI session is picked up at the next session start / daily task, not instantly (no file watcher by design; an always-running watcher would need a service/startup authorization).

## Optional local semantic search (`memory_semantic`) — added 2026-10-16, real-model verified
There was NO embedding code in SecondBrain before this (README: FTS5/BM25 only); the FTS index, writer lease, hash verification and recall pipeline are reused unchanged. Semantic search is an optional layer; FTS works in every state (off, not downloaded, runtime failing).
- **Provider `llama` (default, Hub-manageable, no Ollama needed)**: pinned llama.cpp `llama-server` (b11669 Windows CPU x64, 19.5 MB, sha256 pinned) + pinned GGUF model `bge-m3-Q4_K_M` (438 MB, MIT, multilingual incl. Turkish, sha256 pinned), downloaded by `memory.semantic.pull` into `<data root>/semantic-runtime/` (size + sha256 verified before use, zip path traversal refused, `.part` files removed on failure). The server is started only for one operation on a free loopback port and stopped afterwards: no resident process. Provider `ollama` (an Ollama the user already runs) is kept as an alternative.
- Privacy: any non-loopback endpoint is refused; the only network use is the explicit pinned download. No Python/ML dependency in the frozen distribution (stdlib only).
- Ops: `memory.semantic.status` (read-only), `memory.semantic.configure {confirm, enabled, provider?, model?}` (writes only `semantic.json`), `memory.semantic.pull {confirm}`. Hub (bridge blocks `memory.*`) flow "Onayla, indir ve etkinleştir" = configure -> pull -> `memory.index.refresh` (builds vectors); panel in the SecondBrain settings (`MemoryIndex`).
- Storage: `semantic_index.db` next to the FTS index (one L2-normalised float32 vector per note: title + first 2000 chars); incremental by sha256 after each FTS refresh (`refresh_now`, hooks, daily task, `memory.index.refresh`); deleting it is safe.
- Recall: optional `mode` = `auto` (default: hybrid when enabled and ready, else FTS) | `fts` | `semantic` | `hybrid`; hybrid = reciprocal-rank fusion. Result carries `search {mode, semantic: off|ok|unavailable, reason?}`; provider problems fall back to FTS (explicit `semantic` errors); every hit is still dropped unless the note's sha256 equals the indexed one; recall stays read-only.
- Evidence (isolated root, real model, 2026-10-16, `.build-cache/real_semantic_check.py`): pull 55 s, 8 notes embedded in 4 s; cross-lingual hits FTS cannot make ("vehicle" -> cars.md/garaj.md, "meeting agenda" -> toplanti.md, "veritabani sunucusuz" -> db.md/veritabani.md); no `llama-server` left running. Costs/limits: every recall starts the server (2.6-4.2 s per recall on this CPU); hybrid returns up to `limit` results with no relevance cutoff (weak tail hits possible); one vector per note; Windows x64 runtime only (other platforms: provider ollama).
- Tests: `tests/test_rpp_memory_semantic.py` (fake loopback service, download verification, archive safety, fallback, stale-hit dropping).

## `bounded_recall` (prompt-time "whisper") — evaluated 2026-10-16, deliberately NOT wired
`memory/bounded_recall.py` can append up to 3 notes / 900 characters of vault snippets to every user prompt. Not part of Windows v1: the memory already reaches the user's AI tools at session start (hook context), on demand through the MCP tools and `memory.recall`, and in the Hub memory page; per-prompt injection would send vault text to every client's model on every message, costs tokens, and the module searches through the writable engine without the sha256 verification that `memory.recall` added (a removed passage could still be quoted from the old index). If it is ever wanted it must be: opt-in preference (default off), built on `rpp_memory.run_query` (read-only, hash-verified), limited to the existing 3 notes / 900 characters and its abstention rules, and enabled per client. The module and its tests stay as is.
