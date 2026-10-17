# Research contract fixtures — wire version 1.0

All passages, claims, and implications here are **synthetic examples**, not paper
findings, measured results, or approved advice. Example.com links are locator
fixtures, not sources to fetch.

| Fixture | Expected behavior |
| --- | --- |
| `normal-v1.json` | Accept mixed HTML/PDF evidence, cited summary and conditional business output; preserve HTML null page and PDF page 2; review remains pending. |
| `empty-v1.json` | Accept no evidence and empty insufficient summary/business outputs. Pipeline execution skips generation. |
| `insufficient-v1.json` | Accept available evidence that does not support an answer; empty claims/implications are distinct from retrieval failure. |
| `invalid-v1.json` | Apply each listed mutation independently to `normal-v1.json` and reject: unknown summary/business IDs, negative PDF page, invented HTML page, mismatched PDF page link, or lost HTML heading. |

The invalid fixture records reproducible patches rather than duplicating the full
normal result. `tests/test_research_contracts.py` loads a fresh base for every
mutation. All validators preserve additive fields and original passage text.

See [the contract reference](../../../docs/research-contracts.md) for signatures,
versioning, legacy PDF locator compatibility, and explicit synthetic-source rules.
