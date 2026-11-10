# V4.5.2 — Visual Form & Preflight Integration

- `frontend/components/FormulaEditor.tsx`: table editor with INCI, functional group, bounds, target %, explicit balancing ingredient, errors and unknown-grade warnings.
- `frontend/components/ProtocolEditor.tsx`: protocol form with metric kind, units, user-defined criteria, test days, methods and conditions.
- `frontend/lib/form-model.ts`: frontend validation, non-mutating balance helper and typed scenario models.
- `frontend/app/experiments/page.tsx`/CSS: form-first UI, JSON advanced mode, measured evidence requirements, saved measurement table, preflight review and read-only study snapshot.
- `draft_review_v452.py` and `POST /api/v4.5/review-draft`: read-only preflight via existing V4.4 optimizer, with ambiguity and premix notices.
- `test_v452_integration.py`: 5 new API tests; `frontend/tests/test_form_model.cjs`: 11 assertions.
- `scripts/verify_postgres_v452.py`: optional disposable PostgreSQL integration test; **not executed** without test server.
- `README_V452.md`, `CODEX_HANDOFF_V452.md`, `V452_TEST_REPORT.json`: deployment, validation, Codex next steps.

No existing scientific observation or legal limit was replaced. No external repository was changed.
