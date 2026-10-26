# Public-release review

Reviewed 2026-10-26 08:45 PDT.

Ruff lint/format, JavaScript syntax, all 16 tests, retained source/artifact integrity checks and a complete fresh scientific replay passed. All 126 comparator dossiers and all four recorded pilot dossiers match exactly. No new external model calls were made.

[Review metadata](review.json), [tests](tests.txt), [Ruff](ruff.txt), [format](format.txt), [artifact integrity](integrity.txt), [replay](RESULT.json), [Git-history scan](history-scan.json), [external surfaces](external-surfaces.json).

The reachable Git history was scanned for common credential patterns and accidentally committed environment files, private working directories, runtime records and raw source CSVs. No matches were found by that scan. A later audit on 2026-10-26 found one local working-directory path in `reports/ruff-cleanup-v1/REPLAY-STATUS.json`; the file now records repository-relative paths, and earlier commits still contain the original line. The repositories had no workflow runs, issues or releases at review. README screenshots show laboratory views. Source data attribution and research limitations were reviewed. These bounded checks do not constitute a comprehensive security audit or biological validation.

Only documentation and review evidence changed for publication. Original scientific source and results remain unchanged. Dataset attribution is retained; no project-code licence was assigned. Runtime services remain local applications.
