# Security policy

## Reporting a vulnerability

Do not disclose a suspected vulnerability in a public issue.

Use the private vulnerability-reporting feature of the repository host when it
is available. If this package was distributed through another channel, use the
maintainer's private contact method published by that distributor.

Include:

- affected version;
- reproduction steps;
- expected and observed behavior;
- impact;
- a suggested remediation, if known.

## Supported version

The current `0.1.x` line receives security fixes.

## Demonstration security boundary

The default service:

- binds to `127.0.0.1`;
- has no authentication or multi-user authorization;
- stores fictional demo state in local SQLite;
- serves a reset endpoint intended for demonstrations;
- does not call external services or load remote models.

Do not expose the demo directly to an untrusted network. A production
adaptation must add authenticated identity, role-based authorization, CSRF
protection where cookies are used, rate limits, request-size limits, privacy
controls, secrets management, encrypted transport, operational monitoring, and
backup/restore procedures.

## In-scope examples

- bypassing protected-attribute or appearance-field rejection;
- changing a locked ethical or review policy through the API;
- skipping required human-review transitions;
- rewriting assessment evidence through review routes;
- audit-chain corruption that is reported as valid;
- SQL injection, stored XSS, or unsafe static-file access;
- unexpected external network access or secret disclosure.

## Dependency handling

Dependencies are intentionally small and declared in `pyproject.toml`. Before a
release, run the project validation and an ecosystem-appropriate dependency
audit in a network-enabled trusted environment.

