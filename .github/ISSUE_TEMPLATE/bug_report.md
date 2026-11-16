---
name: Bug report
about: Report something that is broken or behaves incorrectly
title: "[Bug] "
labels: bug
assignees: ''
---

## Describe the bug

A clear, concise description of what the bug is.

## To reproduce

Steps to reproduce the behaviour:

1. Go to '...'
2. Run '...' (exact command, e.g. `uv run uvicorn backend.app.main:app --port 8000`)
3. Open '...' (e.g. the Priority Queue tab)
4. See error

## Expected behaviour

What you expected to happen instead.

## Actual behaviour

What actually happened. Include the full error message, traceback, or console output, not a paraphrase.

<details>
<summary>Logs / traceback</summary>

```text
paste logs here
```

</details>

## Environment

- **Component:** backend API / ETL script / dashboard / Docker Compose / other
- **Commit or branch:** (output of `git rev-parse --short HEAD`)
- **Python version:** (output of `uv run python --version`)
- **Node version:** (output of `node --version`, if dashboard-related)
- **Database:** SQLite (local dev) / PostgreSQL (Docker or Render)
- **OS and version:**

## Screenshots

If the bug is in the dashboard, add screenshots or a short screen recording. Remove any personal or government data before attaching.

## Additional context

Anything else that might help: related issues, recent changes, whether it reproduces on `main`, or a minimal fix suggestion.