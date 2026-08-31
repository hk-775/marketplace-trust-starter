# Deployment guide

## Local evaluation

```bash
./scripts/demo.sh
```

Defaults:

- bind: `127.0.0.1`
- port: `8101`
- database: `data/marketplace_trust_starter.db`

Configuration:

| Variable | Default | Purpose |
|---|---|---|
| `MTS_HOST` | `127.0.0.1` | Bind address |
| `MTS_PORT` | `8101` | Service port |
| `MTS_DATABASE_PATH` | project `data/` database | SQLite path |
| `MTS_PYTHON` | `3.12` | Python version or interpreter selected by `uv` |

## Docker Compose

```bash
docker compose up --build
```

The container:

- listens on `8101`;
- runs as non-root UID/GID `10001`;
- uses a read-only root filesystem;
- drops Linux capabilities;
- writes only to `/data`;
- exposes a health check;
- persists SQLite in a named volume.

Override only the host-side mapping:

```bash
MTS_HOST_PORT=18101 docker compose up --build
```

The service remains on container port `8101`.

## Static publication

Build:

```bash
uv run --locked python scripts/build_site.py
```

Publish the contents of `site/` with any static host. The landing, dashboard,
and architecture pages are derived from the served assets with an explicit
`static` runtime marker. The dashboard loads `assets/demo-data.json` in
read-only mode and does not probe local or private API routes.

Verify before publication:

```bash
uv run --locked python scripts/build_site.py --check
```

No external font, script, image, or API asset is required.

## Target AWS services reference

The downloadable
[AWS services reference architecture](../site/assets/aws-services-reference.drawio)
is planning material only. It maps authentication, private ingress, replicated
compute, managed relational state, immutable audit retention, secrets,
observability, and image delivery to possible AWS services.

This repository does not include AWS infrastructure as code, an AWS deployment
workflow, account-specific identifiers, or deployed resources. See
[Architecture](ARCHITECTURE.md#target-aws-services-reference-architecture) for
the service-by-service boundaries and
[Production readiness](PRODUCTION_READINESS.md) for the gaps that remain.

## Production gaps

The included Docker profile is hardened for local evaluation, not certified
production operation. Before deployment beyond a trusted local environment,
add:

- authentication and role-based authorization;
- tenant and subject isolation;
- TLS termination and trusted proxy configuration;
- CSRF controls if browser sessions use cookies;
- request, rate, and concurrency limits;
- encrypted managed storage and tested backups;
- an external append-only audit destination;
- privacy classification, retention, deletion, and export;
- secrets management;
- queue age and service health monitoring;
- reviewer access controls and wellbeing support;
- policy approval and rollback;
- appeal and correction workflow;
- calibrated evaluation and ongoing false-positive monitoring.

## Replacing SQLite

Multiple replicas should not share the included SQLite file. Preserve these
transactional invariants when moving to another datastore:

- assessment and optional case become visible together;
- case evidence is an immutable assessment snapshot;
- review transitions are compare-and-set operations;
- policy update and version increment are atomic;
- audit order and previous-hash linkage are deterministic;
- seed/reset functionality is disabled outside an explicit demo environment.

## Network posture

The application does not initiate external network calls. A reverse proxy,
identity provider, monitoring exporter, reputation feed, or model integration
changes that posture and must be documented, authenticated, bounded, and tested
separately.
