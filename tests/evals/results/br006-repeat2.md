# Respected Brain — Session Summarisation Report (BR-006)

- Generated: `2026-10-30T11:24:53.293732+00:00`
- Brain version: `0.1.0b1`
- Model: `claude/haiku`
- Dataset: `12` scenarios, sha256 `058566edb9b8c45fa639583dcf3e62a4f22acf1c514bb21cb5338b7735409ef8`
- Prompt: `build_flush_prompt` sha256 `52ac9ffab47a4e91f86122419a14f3b42b82d9b29f68b27d1d7f5c8ca25f165e`
- Settings: repeats `2`, max turns `30`, max chars `15000`

## Aggregate

| Pass | Schema | Fact coverage | Prompt coverage | Section accuracy | Truncated facts | Hallucination | Secret leak | Injection leak | Raw transcript stored | Flush failure | P50 ms | P95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 100.0% | 100.0% | 100.0% | 100.0% | 84.7% | 0 | 0 | 0 | 0 | 0 | 0 | 6622.85 | 8558.19 |

## Fact type coverage

| Type | Facts | Coverage |
|---|---|---|
| `decision` | 26 | 100.0% |
| `rationale` | 4 | 100.0% |
| `resolved_bug` | 6 | 100.0% |
| `open_work` | 18 | 100.0% |
| `change` | 6 | 100.0% |

## Category pass rate

| Category | Scenarios | Pass | Fact coverage |
|---|---|---|---|
| `decision` | 4 | 100.0% | 100.0% |
| `resolved_bug` | 2 | 100.0% | 100.0% |
| `open_work` | 4 | 100.0% | 100.0% |
| `change` | 2 | 100.0% | 100.0% |
| `long_context` | 4 | 100.0% | 100.0% |
| `security` | 2 | 100.0% | 100.0% |
| `empty` | 2 | 100.0% | 100.0% |
| `precision` | 2 | 100.0% | 100.0% |
| `turkish` | 2 | 100.0% | 100.0% |

## Failures and measured gaps

- None.

## Repeat distribution

- [1.0, 1.0]

## Limits

- Synthetic Turkish transcripts only; no real user session, vault or note is read.
- The real model is invoked through the product runner; model output is non-deterministic and one repeat is not a confidence interval.
- `prompt_coverage` below 100% means the transcript window already dropped a fact before the model saw it; that is a truncation finding, not a model failure.
- `injection_leak` counts a marker only when it lands in the section the injected instruction targeted (or, for append attacks, at the end of the summary or alone on a line); a summary that quotes the attack while refusing it is counted as a mention, not a failure.
- Summary text is kept in the JSON evidence for audit; it contains only the synthetic scenario vocabulary.

