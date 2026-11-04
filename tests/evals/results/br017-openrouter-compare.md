# Provider quality comparison

- Dataset: `058566edb9b8c45fa639583dcf3e62a4f22acf1c514bb21cb5338b7735409ef8`
- Base: `claude/haiku` (claude)
- New: `openrouter/openai/gpt-4o-mini` (openrouter)
- Regressions: 5

| Metric | Delta (new - base) |
|---|---:|
| `pass_rate` | -1.0000 |
| `schema_valid_rate` | -1.0000 |
| `fact_coverage` | -1.0000 |
| `prompt_coverage` | +0.0000 |
| `section_accuracy` | -0.6945 |
| `truncated_facts` | +0.0000 |
| `hallucination_scenarios` | +0.0000 |
| `secret_leak_scenarios` | +0.0000 |
| `injection_leak_scenarios` | +0.0000 |
| `raw_transcript_stored` | +0.0000 |
| `flush_failures` | +12.0000 |

| Category | Pass-rate delta | Fact-coverage delta |
|---|---:|---:|
| `decision` | -1.0000 | -1.0000 |
| `resolved_bug` | -1.0000 | -1.0000 |
| `open_work` | -1.0000 | -1.0000 |
| `change` | -1.0000 | -1.0000 |
| `long_context` | -1.0000 | -1.0000 |
| `security` | -1.0000 | -1.0000 |
| `empty` | -1.0000 | -1.0000 |
| `precision` | -1.0000 | -1.0000 |
| `turkish` | -1.0000 | -1.0000 |

## Regressions

- pass_rate 1.0 -> 0.0
- schema_valid_rate 1.0 -> 0.0
- fact_coverage 1.0 -> 0.0
- section_accuracy 0.7778 -> 0.0833
- flush_failures 0 -> 12
