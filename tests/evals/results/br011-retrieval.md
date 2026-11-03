# Respected Brain — Memory Evaluation Report (BR-001)

- Generated: `2026-11-03T03:48:23.049567+00:00`
- Brain version: `0.1.0b1`
- Dataset: `50` scenarios, sha256 `c0cdb91c5e9960da32e09dbdefdd1a574790c2e06d6cfd419bb85b402c60e662`
- Settings: modes `none, fts, hybrid`, repeats `2`, limit `5`, snippet `400`
- Prompt: retrieval-only: synthetic query -> top-k path/title/snippet; no generation model is invoked
- Semantic model: `{'enabled': False, 'provider': 'llama', 'model': 'bge-m3-Q4_K_M'}`

## Aggregate

| Mode | Pass | Hit@1 | Hit@5 | MRR | Answer | Coverage | Stale leak | No-answer | P50 ms | P95 ms | Ctx tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `none` | 16.0% | 0.0% | 0.0% | 0.000 | 0.0% | 0.0% | 0 | 100.0% | n/a | n/a | 0.0 |
| `fts` | 94.0% | 92.9% | 100.0% | 0.964 | 100.0% | 100.0% | 0 | 100.0% | 30.53 | 36.98 | 18.606 |
| `hybrid` | n/a | n/a | n/a | n/a | n/a | n/a | 0 | n/a | n/a | n/a | n/a |

## Category pass rate

| Mode | recall | multi_session | temporal | update | unknown |
|---|---|---|---|---|---|
| `none` | 0% | 0% | 0% | 0% | 100% |
| `fts` | 100% | 100% | 70% | 100% | 100% |
| `hybrid` | n/a | n/a | n/a | n/a | n/a |

## Failures

- `none` / `R01` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R02` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R03` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R04` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R05` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R06` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R07` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R08` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R09` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R10` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R11` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `R12` (recall) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M01` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M02` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M03` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M04` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M05` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M06` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M07` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M08` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M09` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `M10` (multi_session) — expected source outside top-k, answer term missing; got `[]`
- `none` / `T01` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T02` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T03` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T04` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T05` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T06` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T07` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T08` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T09` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `T10` (temporal) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U01` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U02` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U03` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U04` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U05` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U06` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U07` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U08` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U09` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `none` / `U10` (update) — expected source outside top-k, answer term missing, expected source not first; got `[]`
- `fts` / `T01` (temporal) — expected source not first; got `['releases/v1.md', 'releases/v2.md']`
- `fts` / `T02` (temporal) — expected source not first; got `['ops/migrations-2026-05.md', 'ops/migrations-2026-10.md']`
- `fts` / `T07` (temporal) — expected source not first; got `['meetings/july.md', 'meetings/october.md']`

## Repeat distribution

- `none`: [0.16, 0.16] (stdev 0.0)
- `fts`: [0.94, 0.94] (stdev 0.0)
- `hybrid`: [None, None] (stdev 0.0)

## Limits

- Retrieval-level evaluation only: no answer synthesis/judge model, no summary quality claim.
- Semantic mode reports `unavailable` when the local provider is disabled; it is not silently scored as zero.
- Synthetic notes are isolated in temporary directories; the real user vault is never read.

