# Architecture

## Goals

Marketplace Trust Starter optimizes for:

- local reproducibility;
- explainable behavior;
- a small dependency and operational footprint;
- strict separation between detection and human judgment;
- replaceable storage and integration edges.

It does not attempt to be a production-scale moderation platform.

## Components

### Web and API boundary

`marketplace_trust_starter.app` creates the FastAPI application, validates
requests, serves OpenAPI, applies browser security headers, and serves the
landing, dashboard, and architecture assets.

All browser requests are same-origin. The application has no runtime client for
an external service.

### Application service

`marketplace_trust_starter.service`:

1. reads one policy snapshot and version;
2. creates an assessment identifier;
3. invokes the pure engine;
4. creates a case only when the locked review threshold is reached;
5. persists assessment, case, and audit events.

The service recommends workflow steps. It has no irreversible enforcement
adapter.

### Deterministic engine

`marketplace_trust_starter.engine` has no I/O. It accepts a validated request
and a policy map, then returns:

- named risk signals;
- named counter-signals;
- base points, multipliers, and final points;
- evidence strings;
- a clamped 0–100 score;
- low, guarded, high, or critical tier;
- confidence in available evidence;
- review routing and a recommended next step;
- limitations.

Scores are additive and bounded. Threshold and compound-condition choices are
documented in the policy records and tests.

### SQLite store

`marketplace_trust_starter.store` owns:

- schema creation;
- deterministic seed reset;
- policy versioning;
- assessment snapshots;
- review cases and transitions;
- metrics and signal insights;
- audit append and verification.

The default database is `data/marketplace_trust_starter.db`.

## Transactions

### Assessment transaction

A new assessment and its optional case are written in one `BEGIN IMMEDIATE`
transaction. Their audit events are appended before commit. A caller therefore
does not receive an assessment that refers to a missing case.

### Policy transaction

A policy change updates the rule, increments its rule version, increments the
global policy version, and appends an event in one transaction. Existing
assessment JSON remains unchanged.

### Review transaction

Only these transitions are supported:

```text
open -> in_review -> resolved
```

An open case cannot resolve directly. A resolved case is terminal through the
API. Review updates cannot edit subject, score, tier, policy version, or
evidence.

## Audit chain

Each event hash is SHA-256 over canonical JSON containing:

- timestamp;
- actor;
- action;
- entity type and identifier;
- details;
- previous event hash.

The first event uses 64 zeroes as its previous hash. `GET /api/v1/audit`
recomputes the chain in insertion order and returns `chain_valid`.

This is tamper evidence for a starter, not an external immutable ledger. A
production deployment should send audit records to a separately controlled,
append-only destination.

## Static site build

The served source lives under:

```text
src/marketplace_trust_starter/web/
```

`scripts/build_site.py` creates a deterministic API snapshot and mirrors the
landing, dashboard, architecture, and assets into `site/`. The same dashboard
uses the live API when available and the read-only snapshot otherwise.

## Extension points

A production adaptation may replace:

- SQLite with a transactional managed database;
- local audit with an append-only evidence store;
- deterministic rules with calibrated models or external reputation signals;
- local identity with authenticated platform principals;
- the demo review queue with an existing case-management system.

Any replacement should preserve input prohibitions, policy versions, evidence
snapshots, human-review semantics, and benign-regression tests.

## Scale and concurrency limitations

SQLite is appropriate for this local demo and low-concurrency evaluation. It is
not the recommended shared store for multiple service replicas. The API also
lacks job queues, streaming ingestion, distributed locks, tenant isolation,
and archival policy.

