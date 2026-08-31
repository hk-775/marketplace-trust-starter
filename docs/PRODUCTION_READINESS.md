# Production readiness

## Statement

Version 0.1.0 is suitable for local evaluation with synthetic data. It is not
ready to operate a production trust-and-safety program or authorize
consequential marketplace action.

## Readiness ledger

| Area | Status | Current evidence | Production gap |
| --- | --- | --- | --- |
| Deterministic assessment | Implemented locally | Named profile, content, and coordination signals with bounded point math and benign-regression tests | Platform-specific calibration, drift review, and measured error rates |
| Ethical input guard | Implemented locally | Nested prohibited-field rejection and locked policy boundary | Independent review, proxy-discrimination testing, and enforcement across every upstream data path |
| Human review routing | Implemented locally | High/critical cases, named reviewers, enforced transitions, explicit outcomes, immutable resolved cases | Authenticated identity, queue ownership, escalation, quality review, and reviewer wellbeing controls |
| Policy governance | Partial | Versioned rules, locked boundaries, reasons, and audit events | Protected approval workflow, separation of duties, rollback, and jurisdiction-specific policy |
| Evidence snapshots | Implemented locally | Assessment evidence and policy version are retained with each case | Data classification, minimization, encryption, access review, deletion, correction, and legal holds |
| Audit integrity | Partial | Canonical SHA-256 hash chain and verification | External immutable retention, signatures, trusted timestamps, key governance, and independent reconciliation |
| Local persistence | Partial | SQLite transactions, deterministic seed/reset, and state-isolation tests | Managed transactional database, migrations, tenancy, backup/restore drills, and failure testing |
| Authentication | Blocked | None in the demo service | Human and workload identity |
| Authorization | Blocked | None in the demo service | Role-based and tenant-scoped authorization with protected administration |
| Network security | Partial | Localhost default, same-origin UI, security headers, and no outbound runtime calls | TLS, trusted proxy policy, WAF/rate limits, private service boundaries, and egress controls |
| Appeals and correction | Missing | Review outcomes are recorded | Notice, appeal, correction, reinstatement, and accountable final authority |
| Abuse-resistant reporting | Missing | Report counts are accepted as input | Reporter trust, deduplication, brigading defenses, and provenance |
| Privacy and compliance | Not claimed | Synthetic seed data and prohibited sensitive fields | Qualified, context-specific legal/privacy review and documented retention rights |
| Observability | Missing | Health, metrics endpoint, audit view, and local logs | Redacted centralized logs, traces, alarms, service targets, queue-age monitoring, and on-call ownership |
| Availability and recovery | Missing | Local restart and deterministic reset | Multi-AZ design, capacity model, recovery objectives, tested backups, and failover |
| Performance evidence | Missing | Functional tests only | Load tests, concurrency tests, sizing, and latency/error budgets |
| Supply chain | Partial | `uv.lock`, temporary package inspection, pinned GitHub Actions, repository/history scans | Signed releases, SBOM, provenance attestations, image scanning, and dependency response process |
| Static publication | Implemented | Repository-owned assets, explicit static mode, Pages-base browser check, and no public API calls | Accessibility review and ongoing published-site monitoring |
| Security testing | Partial | Negative tests, credential-shaped scans, history scan, and local release checks | Independent assessment, SAST/dependency audit, fuzzing, and incident exercises |
| Support operations | Missing | Community support and security-reporting documents | Staffing, response targets, escalation, incident communications, and service ownership |

## Blocking risks

1. The service has no authentication, authorization, tenant isolation, or
   production identity source.
2. The reset, policy, review, evidence, and audit routes are reachable by any
   caller that can reach the demonstration service.
3. SQLite and the local hash chain do not provide distributed consistency,
   durable external retention, or protection from a privileged host operator.
4. No representative evaluation establishes false-positive, false-negative,
   fairness, or operational-harm bounds for a real marketplace.
5. Appeals, correction, reinstatement, reviewer quality controls, and final
   enforcement authority are outside the implementation.
6. Personal-data classification, retention, deletion, export, and legal
   requirements are not implemented.
7. Monitoring, incident response, backup/restore, capacity, and recovery
   objectives are absent.

## Maturation sequence

The
[target AWS services reference architecture](ARCHITECTURE.md#target-aws-services-reference-architecture)
maps these gaps to one possible deployment shape. It is planning material only:
this repository contains no AWS infrastructure as code and creates no cloud
resources.

### Evaluation hardening

- build representative, consented, platform-specific evaluation sets;
- measure false positives, false negatives, queue effects, and proxy harms;
- add property, fuzz, concurrency, migration, backup, and accessibility tests;
- conduct manual privacy, safety, and security review.

### Authenticated non-production service

- add verified human and workload identities;
- enforce role, tenant, and subject boundaries;
- move state to a managed transactional database;
- retain signed audit exports in a separately controlled immutable store;
- integrate a real case-management and appeal workflow without automated
  irreversible enforcement.

### Operational validation

- define service targets from measured workloads;
- implement redacted observability, alerting, incident ownership, and recovery;
- exercise key rotation, backup restoration, failover, rollback, and policy
  change approval;
- run an independent security assessment and low-sensitivity pilot.

### Production decision

Production use requires explicit acceptance by accountable engineering,
security, operations, privacy, legal, trust-and-safety, and business owners.
Repository checks alone are not production evidence.
