# Domain Documentation

## Layout: Single-Context

This repository uses a **single-context** domain documentation layout:

- **GLOSSARY.md** (repo root): Centralized domain terminology, shared across the project
- **docs/adr/**: Architecture Decision Records
- **docs/agents/**: Agent configuration (this file, issue-tracker.md, triage-labels.md)

## Consumer Rules

1. **Single source of truth**: All domain terminology lives in `GLOSSARY.md` at the repo root.
2. **ADRs are immutable**: Once written, ADRs are never modified; new ADRs supersede old ones.
3. **Agent context**: All `docs/agents/*.md` files are authoritative for agent behavior.
4. **Cross-references**: Use `[[page:<id>]]` syntax for internal links in markdown files.

## No Multi-Context

This is **not** a multi-context repository (no `GLOSSARY-MAP.md` at root, no per-subproject `GLOSSARY.md` files). The entire project shares a single glossary and ADR directory.
