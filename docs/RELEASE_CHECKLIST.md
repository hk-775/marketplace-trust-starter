# Release checklist

This checklist coordinates a repository and source release. Completing it does
not make Marketplace Trust Starter production ready.

## Scope and governance

- [ ] Version and release scope are documented.
- [ ] Changelog entries match implemented behavior.
- [ ] Safety-sensitive rule, threshold, review, or policy changes have explicit
      maintainer review.
- [ ] A security reviewer approved the release.
- [ ] Blocking issues are resolved or explicitly deferred.

## Provenance and licensing

- [ ] Every contribution has a known compatible origin.
- [ ] License and notice files are current.
- [ ] No personal, customer, confidential, or production material is present.
- [ ] Seed data, examples, screenshots, and identifiers remain fictional.
- [ ] No prohibited biometric, face, appearance, attractiveness, or
      protected-attribute inference artifact is present.

## Implementation

- [ ] Input prohibitions and locked ethical boundaries match documentation.
- [ ] High and critical scores still route to human review.
- [ ] No irreversible automated enforcement adapter was introduced.
- [ ] Review state transitions and resolved-case immutability remain enforced.
- [ ] Policy and data migration implications are documented.
- [ ] New dependencies have a documented purpose and compatible license.

## Validation

- [ ] Tests pass on Python 3.11, 3.12, and 3.13.
- [ ] Branch coverage is at least the configured threshold.
- [ ] `uv sync --locked` succeeds from a clean checkout.
- [ ] All Python validation runs through `uv run --locked`.
- [ ] Repository and credential-shaped scans pass.
- [ ] Reachable Git history scan passes without skipped blobs.
- [ ] Gitleaks scans the worktree and history successfully, or unavailability
      is disclosed.
- [ ] Git object integrity and whitespace checks pass.
- [ ] Workflow actions are pinned to full commit identifiers.
- [ ] Static/service publication modes and mirrors are current.
- [ ] Exact Pages-base browser, interaction, download, mobile, and
      prohibited-network checks pass.
- [ ] The seeded service smoke test restores canonical state.
- [ ] Temporary wheel and source archives build and contain required members.
- [ ] No generated archive, database, cache, coverage output, or environment
      remains in the repository.

## Security and operations

- [ ] Security policy and private reporting are configured.
- [ ] Production-readiness ledger is honest and current.
- [ ] No unresolved high-severity vulnerability is known.
- [ ] Dependency and container audits were run in a trusted, network-enabled
      environment.
- [ ] Manual keyboard, contrast, and basic screen-reader review is complete.

## Publication

- [ ] Repository description, topics, homepage, and support links are current.
- [ ] Default branch protection requires CI and pull-request review.
- [ ] Public-site claims match implemented evidence.
- [ ] Current logical and target AWS architecture downloads open.
- [ ] The AWS diagram remains labeled target/reference and does not imply
      deployed infrastructure or AWS endorsement.
- [ ] The `github-pages` environment has required reviewers before launch.
- [ ] Pages deployment is manually started from reviewed `main`.
- [ ] Published routes, assets, and byte hashes are verified after deployment.
- [ ] Release tag and package version agree if a tagged release is created.

## Post-release

- [ ] The quickstart is tested from the public source.
- [ ] Release notes link to limitations, ethics, readiness, and security
      reporting.
- [ ] Known issues and support expectations are communicated.
