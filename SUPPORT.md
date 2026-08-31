# Support

Marketplace Trust Starter is a community open-source alpha project. It has no
paid support, uptime commitment, response guarantee, or production service.

## Where to ask

- Use the
  [question form](https://github.com/hk-775/marketplace-trust-starter/issues/new?template=question.yml)
  for reproducible, non-sensitive usage questions.
- Use the
  [bug form](https://github.com/hk-775/marketplace-trust-starter/issues/new?template=bug.yml)
  for incorrect behavior.
- Use private vulnerability reporting as described in
  [SECURITY.md](SECURITY.md).

Before asking, run:

```console
uv sync --locked --python 3.12
make test
make scan
```

Include the operating system, Python version, command, machine-readable error,
and a minimal synthetic reproduction. Do not attach a database containing
personal, customer, marketplace, or production information.

## Scope

Community support can reasonably cover:

- local setup on Python 3.11–3.13;
- the deterministic assessment and review workflow;
- policy, audit, seed-reset, and static-site behavior;
- repository tests and publication checks; and
- documentation corrections.

It does not cover:

- production deployment or security architecture;
- legal, regulatory, certification, or compliance advice;
- incident response for third-party systems;
- moderation policy decisions or reviewer staffing; or
- recovery guarantees for corrupted or lost data.
