# Public repository security review

Reviewed on 2026-09-28 for the educational, local Docker Compose lab. This
review covers tracked source, workflows, configuration, Git history, and all
four published screenshots. It does not certify a production SIEM.

| File / location | Issue | Severity | Resolution |
| --- | --- | --- | --- |
| `.gitignore` (previously only `.env` and `logs/*` among private data patterns) | Alternate environment files, keys, captures, databases, archives, and VM media could be added accidentally. No such file was found tracked. | Low | Added patterns for these artifact types while preserving `.env.example` and `logs/.gitkeep`. |

## Must fix before commit

- [x] Keep `.env` and generated `logs/security-events.jsonl` ignored. The local
  Grafana password is populated and does not match the example or common
  defaults; its value was not copied into this report.
- [x] Inspect screenshots for credentials and identifying information. The
  four tracked images show synthetic accounts and RFC 5737 documentation IPs.
- [x] Check Git history for private file paths and common credential patterns.
  The 105-object local history check found only documented placeholder and CI
  validation assignments; no private key, token, or real credential was found.
- [x] Retain local-only host port mappings, required Grafana password, disabled
  anonymous access, and explicit educational-use warnings.
- [x] Preserve pinned GitHub Actions, read-only checkout credentials, minimal
  workflow permissions, CodeQL, Bandit, and the existing CI gate.

## Reviewed configuration limitations

`loki/config.yml` sets `auth_enabled: false`, and Alloy listens on `0.0.0.0`
inside its container. Compose publishes their host ports only on `127.0.0.1`.
Processes on the host or Compose bridge can therefore reach lab interfaces.
The repository must continue using synthetic logs; these settings are not
appropriate for a shared or production deployment. The README and
`SECURITY.md` disclose the production limitations.

## Verification and scope limits

Seven Python tests and Docker Compose configuration validation passed locally.
The GitHub `main` commit reviewed before this change had successful Tests,
Bandit, and CodeQL workflows. The active ruleset requires a pull request and
the `CI Gate` status. The connected GitHub integration could not read the
code-scanning alert queue, so its open-alert state is unverified. Runtime
Docker service behavior and the private contents of ignored `.private/` and
generated log files were outside this publication review.
