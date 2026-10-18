# Privacy and client-config ownership (audit P0 #5, #6 and categories A1, A2, A4, A5)

Status: implemented 2026-10-17.

## MCP note writing needs the user's permission (A1)
`respected_quick_capture` and `respected_remember` were writing straight into the vault (`Knowledge`, `Projects`, `Inbox/Dump`) for any
connected model. Now:
* The setting **`mcp_write`** (default **off**, Hub settings form) is the user's permission. It is read fresh on every call, so switching it off
  closes the door at once. Off: the tools are not even listed and calls return an explanatory error.
* On: notes go to one fixed inbox, `850-Companion/Inbox/MCP`, through the same creator as the authorised RPP write (never overwrites, 500-note cap,
  ownership front matter `source: mcp`, `review: pending`, a stored operation record). `respected_remember` fields (`scope`, `confidence`,
  `supersedes`, `project`) become front-matter metadata only; `confidence: verified` is stored as `inferred` (a model cannot vouch for itself).
  Nothing is promoted into curated folders automatically.
* `respected_revert_note` (listed only when writes are on) removes a note the MCP wrote, refusing when the user edited it.

## Session transcripts are not copied by default (A2)
* PreCompact no longer copies transcripts into the vault. **`archive_transcripts`** (default off) opts in; the copy then lives in the technical
  data root (`session-archive/`), never the vault (nothing syncs or publishes it), is redacted, and is purged after
  **`transcript_retention_days`** (default 14, 1-90). `capture_mode = manual` still copies nothing.
* `memory/redact.py` removes private-key blocks, JWTs, bearer/basic credentials, provider tokens (OpenAI/Anthropic/GitHub/HF/Slack/AWS/Google/npm),
  credentials in URLs and `name = value` pairs whose name says secret (English and Turkish). It runs on the transcript before it reaches any
  summariser CLI, on the summary before it is written to daily/Last-Session/Threads, and on archives. Best effort: a password written as plain
  prose is not recognised, which is why the archive is opt-in.
* The summary prompt delimiters carry a random per-request code, so a transcript cannot close the data block.

## Undoing only our entries in client configs (A4) and keeping no copies of them (A5)
* `integrations/delta.py` describes what we changed in a client's file as a **delta**: for JSON, partial trees (changed keys; added/removed list
  items); for TOML/Markdown/anything else, line operations (inserted/replaced/removed lines). `ExternalChange.undo()` applies it to whatever the
  file looks like now: our entries go, the client's later rewrites and the user's additions stay. A JSON/text entry the user *edited* is a conflict
  (nothing is changed); a block the user already removed is a no-op; a file we created is deleted only when nothing else was added to it.
  Scheduled tasks, shortcuts and registry values stay exact-match-or-conflict.
* Persistence: the ownership manifest stores the delta + SHA-256 fingerprints, **not** the files. Transaction journals keep the complete images only
  while a transaction can still roll back; at commit they are compacted the same way (`scrub_committed_journals` also upgrades journals written by older
  versions at uninstall). A secret that lives in another tool's entry of `~/.claude.json` therefore never ends up in `install-manifest.json` or
  `backups/tx-*`. Verified with a real install/uninstall in `respected-hub/src-tauri/tests/brain_e2e.rs`.

## Backup and restore (category B)
`maintenance backup_restic` (restic, opt-in): needs an explicit password source, initialises a new repository, verifies a backup by restoring it and
comparing every file's SHA-256, and **`--restore-to NEW_EMPTY_FOLDER [--snapshot ID]`** restores into a folder that is new or empty and outside the
vault. The vault is never overwritten; the user copies back what they want. Proven against a functional restic stand-in (`tests/test_backup_restore.py`);
a run against real restic is a release-phase check.

## Limits
* JSON written by a client is re-serialised with two-space indentation when we undo (semantically identical; Claude Code writes the same shape).
* Prompt injection through memory is mitigated (redaction, random delimiters, review inbox), not eliminated; the summariser CLI keeps its own
  read-only sandbox.
