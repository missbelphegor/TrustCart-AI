# Latency report

Queries: 200

| Stage | p50 ms | p95 ms | max ms |
|---|---:|---:|---:|
| t_total | 0.37 | 0.61 | 3.36 |
| t_normalize | 0.14 | 0.22 | 1.47 |
| t_retrieve | 0.07 | 0.12 | 0.88 |
| t_gate | 0.00 | 0.00 | 0.00 |
| t_verify | 0.16 | 0.31 | 1.01 |

Mean input/output tokens: 0 / 0
Mean LLM calls: 0
LLM skipped: 100%
Verifier rescues: 0.0%

## Cost optimisation
Rules-first parsing and response templates avoid model initialization and calls. Hashed local vectors avoid downloading or loading embedding weights.