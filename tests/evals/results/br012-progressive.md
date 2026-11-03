# Respected Brain — Progressive Context Report (BR-012)

- Generated: `2026-11-03T04:05:32.990441+00:00`
- Brain version: `0.1.0b1`
- Dataset sha256: `c0cdb91c5e9960da32e09dbdefdd1a574790c2e06d6cfd419bb85b402c60e662`
- Settings: limit `5`, snippet `400`, budgets `[600, 120, 60]`, padded note chars `3000`

## Views

| View | Pass | Hit@1 | Hit@5 | MRR | Answer | Stale | No-answer | Tokens | vs full | Failures |
|---|---|---|---|---|---|---|---|---|---|---|
| `search` | 98.0% | 97.6% | 100.0% | 0.988 | 100.0% | 0 | 100.0% | 47.452 | 0.04x | T01 |
| `full` | 98.0% | 97.6% | 100.0% | 0.988 | 100.0% | 0 | 100.0% | 1103.458 | 1.00x | T01 |
| `compact-600` | 98.0% | 97.6% | 100.0% | 0.988 | 100.0% | 0 | 100.0% | 47.452 | 0.04x | T01 |
| `compact-120` | 98.0% | 97.6% | 100.0% | 0.988 | 100.0% | 0 | 100.0% | 47.452 | 0.04x | T01 |
| `compact-60` | 80.0% | 97.6% | 100.0% | 0.988 | 78.6% | 0 | 100.0% | 29.186 | 0.03x | M01, M03, M04, M05, M06, M07, M08, M09, M10, T01 |

## Notes

- `search` is the current top-k snippet result; `full` reads every top-k note body (naive baseline).
- `compact-*` is the same ranked hits passed through `memory.context.build_context` at that token budget.
- Answer-bearing note text is unchanged; irrelevant prose pads each note to at least `pad_chars` so full-note reads represent long real notes.
- Accuracy uses the BR-001 scenario rules; tokens are snippet characters / 4 (same metric as the harness).
