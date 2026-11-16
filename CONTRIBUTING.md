# Contributing to WaterTriage

Thanks for helping improve WaterTriage. This is an academic NTCC minor project (ETMN100) on water-quality risk scoring for Uttar Pradesh and Bihar, so contributions that touch the scoring model or the data corpus need extra care — reported figures depend on them.

## Before you start

1. **Check existing issues.** Search [open issues](https://github.com/anubhavaanand/water-triage/issues) before filing a new one. If an issue already covers your idea, comment on it instead of opening a duplicate.
2. **For anything non-trivial, open an issue first.** This avoids two people solving the same problem in different ways. Small fixes (typos, doc corrections, obvious bugs) can go straight to a pull request.
3. **Read [AGENTS.md](AGENTS.md) and [DESIGN.md](DESIGN.md)** for the current project state, the frozen scoring model, and architecture decisions. Decisions listed as "Do NOT Re-Open" in AGENTS.md are settled; changing them needs a maintainer discussion first.

## Reporting bugs and requesting features

Use the issue templates — they appear automatically when you open a [new issue](https://github.com/anubhavaanand/water-triage/issues/new/choose):

- **[Bug report](.github/ISSUE_TEMPLATE/bug_report.md)** — for broken behaviour. Include reproduction steps, the exact command, environment details, and logs or a traceback.
- **[Feature request](.github/ISSUE_TEMPLATE/feature_request.md)** — for new capabilities. Include the problem, the proposed solution, alternatives considered, and which part of the system it touches.

Blank issues are disabled so that every report arrives with repro steps and version information. Do not use issues for anything security-related — see [SECURITY.md](SECURITY.md).

## Pull requests

1. Fork the repository and create a branch from `main`.
2. Make focused, minimal changes. One logical change per pull request.
3. Follow the existing code conventions:
   - **Python** ≥ 3.13, dependencies managed with `uv`. Edit `pyproject.toml`, then run `uv sync`.
   - **No code comments** unless a comment is genuinely needed to explain non-obvious logic.
   - **React** components follow the existing patterns in `dashboard/src/`.
4. Run the checks before pushing:
   ```bash
   uv run pytest backend/tests
   cd dashboard && npm run build
   npx playwright test
   ```
5. Open the pull request with a clear description of what changed and why. Reference the issue it closes (`Closes #NN`).
6. Do not commit `.env`, database files, or any credential. `.env` is gitignored and must stay that way.

## Making changes to the scoring model

The scoring model is **frozen** as of commit `7331a9b` (Oct 9, 2026) and is documented in [AGENTS.md](AGENTS.md) section 2.4. Before proposing a change:

- Explain the domain reasoning against **BIS IS 10500** limits.
- State whether the change alters existing risk scores or band assignments — those numbers appear in the final report and must be regenerated if they change.
- Include tests covering the boundary conditions (severity clamping at 0–1, escalation rules, below-detection-limit handling for arsenic, E. coli, and total coliform).

## Making changes to the data corpus

Data comes from WQMIS (UP + Bihar) and is loaded via the ETL scripts in `backend/etl/` and `scripts/`.

- Do not hand-edit generated JSON fallbacks in `dashboard/public/` — regenerate them with `uv run python scripts/regen_fallbacks.py` so the corpus and the dashboard stay consistent.
- Never commit real personal data. Village-level records must be aggregated or anonymised.
- If you change the parser, add or update a fixture test in `backend/tests/`.

## Commit messages

Use a short prefix describing the area of change:

```
feat: <new capability>
fix: <bug fix>
docs: <documentation only>
data: <corpus or generated data change>
test: <tests only>
chore: <tooling, deps, cleanup>
security: <security fix or hardening>
```

Keep the subject line under 72 characters and explain the *why* in the body when it is not obvious.

## Code of conduct

Be respectful and constructive. Report unacceptable behaviour privately to the maintainer rather than in a public thread.