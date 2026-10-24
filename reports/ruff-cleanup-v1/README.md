# Ruff maintenance verification

Verified 2026-10-24 16:16 PDT with Ruff 0.17.2.

- `ruff check .`: passed.
- `ruff format --check .`: passed.
- `python3 -m unittest discover -s tests -v`: 16 passed.
- `python3 scripts/verify_results.py`: passed.
- Complete scientific replay: passed. All 126 comparator metrics, decisions and dossiers match; all four recorded pilot observation sequences and dossiers match. Zero new model calls.

The cleanup formats Python, sorts imports, removes unused imports, and replaces redundant collection constructors with literals or comprehensions. Invalid request/command objects continue to raise the existing `ValueError`; the narrow `TRY004` suppressions document that public validation contract. Scientific parameters, methods, original reports, data and failure cases are preserved.

`source-revision.json` records the initial Git commit and the exact original/current scientific source hashes. The original frozen manifests remain unchanged. Verification accepts only the original hashes or this explicit maintenance mapping, and tests reject unrecorded source changes or a different original study. The replay receipts below supply the result equivalence evidence; the mapping itself is a provenance record.

See [tests](tests.txt), [lint](ruff-check.txt), [format check](ruff-format.txt), [artifact integrity](integrity.txt), [replay](reproduction/RESULT.json), and [verification metadata](verification.json). The top-level `SHA256SUMS` covers this maintenance evidence and the current source. Previous source is retained in the initial Git commit.
