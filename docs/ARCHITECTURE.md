# Architecture

## Goals

Marketplace Trust Starter optimizes for:

- local reproducibility;
- explainable behavior;
- a small dependency and operational footprint;
- strict separation between detection and human judgment;
- replaceable storage and integration edges.

It does not attempt to be a production-scale moderation platform.

## Current logical architecture

![Marketplace Trust Starter current logical architecture](../site/assets/architecture.png)

The diagram above is the implemented version 0.1.0 boundary. Its editable
source is
[`site/assets/architecture.drawio`](../site/assets/architecture.drawio).
The public static build is a separate read-only surface: it uses checked-in
synthetic JSON and does not call the service API.

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
landing, dashboard, architecture, and assets into `site/`. Served pages carry
an explicit `service` runtime marker. The build changes that marker to
`static`; static JavaScript then loads only `assets/demo-data.json` and never
probes an API route.

## Extension points

A production adaptation may replace:

- SQLite with a transactional managed database;
- local audit with an append-only evidence store;
- deterministic rules with calibrated models or external reputation signals;
- local identity with authenticated platform principals;
- the demo review queue with an existing case-management system.

Any replacement should preserve input prohibitions, policy versions, evidence
snapshots, human-review semantics, and benign-regression tests.

## Target AWS services reference architecture

![Marketplace Trust Starter target AWS services reference architecture](../site/assets/aws-services-reference.png)

This diagram is a **target reference, not a deployed topology**. Version 0.1.0
contains no AWS infrastructure as code, AWS account identifiers, resource
names, endpoints, or deployment automation. Publishing the repository or its
Pages site creates no AWS resources.

The editable source is
[`site/assets/aws-services-reference.drawio`](../site/assets/aws-services-reference.drawio).

| Documented gap | Target mapping | Boundary |
| --- | --- | --- |
| Public web delivery and coarse request filtering | Amazon CloudFront, AWS WAF, and a private Amazon S3 origin | Static assets remain read-only; WAF is not application authorization |
| Human and workload identity | Amazon Cognito user pools with authorization code plus PKCE for people and a separate scoped confidential client for machine callers | Tenant, reviewer, policy-admin, and support roles still require an application authorization model |
| Authenticated API boundary | Amazon API Gateway HTTP API with a JWT authorizer | Request schemas, size limits, throttles, and abuse controls must be designed from measured traffic |
| Private application ingress | API Gateway VPC Link to an internal Application Load Balancer | The load balancer is not public and does not replace identity or tenant checks |
| Replicated service runtime | The current FastAPI package in Amazon ECS tasks on AWS Fargate across multiple Availability Zones | The image must disable demo reset and seed behavior outside an explicit demo environment |
| Transactional shared state | Amazon Aurora PostgreSQL-compatible edition | A new persistence adapter, migrations, backup/restore, tenant isolation, and concurrency tests are required |
| Separately retained audit evidence | A scheduled or event-driven exporter writes versioned records to Amazon S3 Object Lock with AWS KMS encryption | Retention, legal hold, signing, reconciliation, and key policies require accountable security design |
| Runtime credentials | AWS Secrets Manager references available only to the required task role | Workflow content, evidence, ordinary configuration, and database rows do not belong in the secret store |
| Operational visibility | Amazon CloudWatch logs, metrics, dashboards, and alarms plus AWS CloudTrail for AWS API activity | Logs and traces require classification, redaction, retention, and access review before real data |
| Reproducible container delivery | GitHub Actions uses short-lived AWS OIDC credentials to publish a scanned, immutable digest to Amazon ECR and update ECS | The repository includes no such deployment workflow; target delivery requires environment approval and rollback |
| Marketplace action | A bounded adapter sends a reviewed recommendation to the host platform | The host platform retains enforcement, notice, correction, appeal, and final human authority |

The reference deliberately keeps detection and review separate from final
enforcement. A high score can create review work; it cannot directly ban,
suspend, delist, seize funds, or otherwise execute an irreversible action.

## Scale and concurrency limitations

SQLite is appropriate for this local demo and low-concurrency evaluation. It is
not the recommended shared store for multiple service replicas. The API also
lacks job queues, streaming ingestion, distributed locks, tenant isolation,
and archival policy.
