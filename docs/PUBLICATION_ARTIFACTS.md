# Publication artifacts

## Purpose

This inventory defines the complete public artifact set for Marketplace Trust
Starter. Every listed artifact is maintained from repository source and can be
validated without private services, production credentials, or customer data.

## Public set

| Artifact | Purpose | Canonical source |
| --- | --- | --- |
| Repository overview | Product boundary, quick evaluation, limitations, and document index | `README.md` |
| Guided evaluation | Locked setup, product walkthrough, API examples, and Docker option | `QUICKSTART.md` |
| Public project site | Product summary and read-only synthetic dashboard | `site/index.html`, `site/dashboard.html` |
| Architecture explorer | Interactive local flows plus downloadable diagrams | `site/architecture.html` |
| Current logical architecture | Local FastAPI, deterministic engine, SQLite, human review, audit, and static-publication boundary | `site/assets/architecture.drawio`, `site/assets/architecture.png` |
| Target AWS services reference | Clearly labeled, not-deployed mapping from production gaps to possible AWS services | `site/assets/aws-services-reference.drawio`, `site/assets/aws-services-reference.png` |
| Long-form architecture | Components, transaction semantics, trust boundaries, AWS target mapping, and scale limits | `docs/ARCHITECTURE.md` |
| Responsible-use material | Prohibited uses, false-positive controls, human authority, and maturation requirements | `docs/ETHICS.md`, `SECURITY.md` |
| Readiness ledger | Implemented evidence, gaps, blocking risks, and maturation sequence | `docs/PRODUCTION_READINESS.md` |
| Browser publication check | Exact Pages-base routes, interactions, mobile layout, downloads, and prohibited-network checks in Chrome | `tools/browser_check.py` |
| Repository and history checks | Required artifacts, formatting, credentials, workflow pins, publication mode, and reachable Git blobs | `tools/repo_scan.py`, `tools/history_scan.py` |
| Package dry run | Temporary wheel/source build, member inspection, and SHA-256 output | `tools/package_check.py` |
| Release checklist | Human coordination for scope, safety, provenance, validation, and publication | `docs/RELEASE_CHECKLIST.md` |

## Visual source of truth

- `src/marketplace_trust_starter/web/assets/architecture.drawio` is the
  editable current logical architecture.
- `src/marketplace_trust_starter/web/assets/architecture.png` is its rendered
  public image.
- `src/marketplace_trust_starter/web/assets/aws-services-reference.drawio` is
  the editable target AWS services reference.
- `src/marketplace_trust_starter/web/assets/aws-services-reference.png` is its
  rendered public image.
- `scripts/build_site.py` mirrors all four files byte-for-byte into
  `site/assets/`.

The project site uses only repository-owned runtime assets. It loads no remote
fonts, scripts, images, telemetry, or network APIs. Static publication mode
loads only the checked-in synthetic snapshot and never probes local or private
API routes.

## Source-distribution inclusion

The source distribution must contain:

- the landing page, dashboard, and architecture explorer;
- the shared stylesheet, JavaScript, icon, and synthetic snapshot;
- both editable draw.io sources and both PNG renders;
- the committed `uv.lock`;
- the public governance, security, readiness, and release documents;
- the browser, repository, history, and package checks; and
- the pinned CI and manually dispatched Pages workflows.

The wheel contains the served web experience and architecture assets.
`tools/package_check.py` enforces both archive boundaries.

## Validation

Before publication:

```console
uv sync --locked --python 3.12
make check
./scripts/validate.sh
```

For an already published site:

```console
uv run --locked python tools/browser_check.py \
  --base-url https://hk-775.github.io/marketplace-trust-starter/
```

## Intentional omissions

Version 0.1.0 does not include AWS infrastructure as code, deployed cloud
resources, production dashboards, identity configuration, trained models,
real marketplace data, signed releases, or a language-registry publication.
The AWS services diagram is target-state planning material; it is not evidence
that those services or controls exist.
