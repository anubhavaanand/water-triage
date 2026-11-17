# Security Policy

WaterTriage handles government water-quality data and deployment secrets (PostgreSQL credentials, API tokens, environment files). We take vulnerabilities in the application and in the data pipeline seriously.

## Supported Versions

Security fixes are applied to the latest commit on `main`. This project is an academic NTCC minor project with no formal release cadence, so only the current `main` state is supported. There are no maintained release branches or long-term support versions.

| Version | Supported |
| --- | --- |
| `main` (latest) | Yes |
| Any tagged or dated snapshot (e.g. report submissions) | No |

If you are running a fork or a self-hosted deployment, update to the latest `main` before reporting an issue, and confirm the problem still reproduces.

## Reporting a Vulnerability

**Do not open a public GitHub issue, pull request, or discussion for a security vulnerability.** Public reports expose the issue to everyone before a fix is available.

Instead, report privately through one of these channels, in order of preference:

1. **GitHub Security Advisories (preferred).** Use the repository's **Security → Report a vulnerability** tab to open a private advisory. This keeps the report private and links the eventual fix to the advisory.
2. **Private email.** Email the maintainer at **anubhavanand354@gmail.com** with the subject line `[SECURITY] WaterTriage`. If you need a PGP key or an alternate channel, say so in your first message and one will be provided.
3. **GitHub private message.** Contact the maintainer directly via their GitHub profile (`@anubhavaanand`).

Please do not include exploit details, credentials, or affected user data in any public channel while the issue is unresolved. If you are unsure whether something is a vulnerability, report it privately and let the maintainer triage it.

### What to Include in a Report

A useful report lets us reproduce and fix the issue without a long back-and-forth. Please include as much of the following as you can:

- **Description** of the vulnerability and its suspected impact (e.g. credential disclosure, SQL injection, unauthorised data access).
- **Affected component and version**: commit SHA or branch, deployment target (Docker Compose, Render, GitHub Pages), and whether it affects the backend API, the ETL scripts, the dashboard, or the data files.
- **Reproduction steps**: the exact request, command, or input, including a minimal payload where relevant. Note any authentication or configuration required.
- **Evidence**: relevant HTTP request/response pairs, log excerpts, or screenshots. Redact real secrets and personal data before attaching anything.
- **Environment**: browser and version, Python version, Docker image tags, and database engine if relevant.
- **Impact assessment**: who is affected, whether data or credentials are exposed, and whether the issue is reachable without authentication.
- **Suggested remediation**, if you have one, and whether you are willing to be credited in the fix commit or advisory.

Incomplete reports are still welcome; we will ask follow-up questions rather than discard them.

## Response Timeline

This is a volunteer academic project, so timelines are best-effort rather than contractual. As a guide:

| Stage | Target |
| --- | --- |
| Initial acknowledgement of a private report | Within **7 days** |
| Triage and severity assessment | Within **14 days** of acknowledgement |
| Fix or mitigation plan shared with the reporter | Within **30 days** for critical issues, **60 days** otherwise |
| Fix released to `main` | As soon as the fix is validated; complex issues may take longer, with status updates at least every 30 days |

Critical issues — exposed credentials, remote code execution, unauthenticated data access, or anything that could expose personal or government data — are prioritised ahead of routine work. If a fix will take longer than the target, we will tell you why and give a revised estimate rather than leaving the report silent.

Coordinated disclosure is preferred: we will credit reporters who want it, and we ask that public details be held until a fix is on `main` or the maintainer agrees otherwise.

## Scope

In scope:

- The FastAPI backend and its API endpoints.
- The ETL and ingestion scripts in `scripts/` and `backend/etl/`.
- The React/Vite dashboard, including any XSS or data exposure in rendered output.
- Deployment configuration in `docker-compose.yml`, Dockerfiles, and CI workflows.
- Committed data files that may contain secrets, personal identifiers, or credentials.

Out of scope:

- Vulnerabilities in third-party services we do not control (GitHub, Render, Docker Hub, PostgreSQL images).
- Findings that require physical access, a compromised host, or a malicious maintainer.
- Reports about missing headers, TLS configuration, or best-practice hardening with no demonstrated exploit, unless they expose data or credentials.
- Automated scanner output without a reproducible impact.

## Handling of Secrets

If you discover a committed secret — a database password, API token, or `.env` content — report it privately and immediately. Do not open a public issue, and do not open a pull request that merely deletes or rotates the secret while the history still contains it, since that does not remove it from git history. The maintainer will rotate the credential and rewrite history as needed.

Rotation steps for a leaked credential:

1. Revoke or rotate the credential at the source (PostgreSQL role, provider token, etc.).
2. Confirm the old value no longer works.
3. Purge the value from git history and force-push only the affected branches, coordinating with anyone who has a clone.
4. Verify with a fresh clone that the secret is no longer reachable.