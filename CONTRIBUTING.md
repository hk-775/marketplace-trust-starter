# Contributing

Thank you for helping improve Marketplace Trust Starter.

## Development setup

Use Python 3.11–3.13 and `uv`:

```bash
uv sync --locked --python 3.12
```

Run the product:

```bash
./scripts/demo.sh
```

Run all local checks:

```bash
./scripts/validate.sh
```

## Design expectations

Changes should preserve these boundaries:

- observable behavior and content, not protected-attribute inference;
- no face, biometric, attractiveness, beauty, or appearance scoring;
- explainable point contributions and policy versions;
- precision-sensitive tests for ambiguous rules;
- human review before consequential decisions;
- fictional examples and seed data;
- no embedded credentials or remote runtime dependency;
- no generated dependencies, caches, or binaries in source control.

## Adding or changing a signal

1. Describe the exact observable evidence and expected abuse pattern.
2. Document likely benign explanations and false-positive controls.
3. Keep the point contribution bounded.
4. Add a named policy record.
5. Add positive and benign tests.
6. Update `docs/ETHICS.md`, `docs/API.md`, or
   `docs/ARCHITECTURE.md` when the product contract changes.
7. Rebuild the static mirror with
   `uv run --locked python scripts/build_site.py`.

## Pull requests

Keep changes focused. Include:

- the user or operator outcome;
- tests run;
- responsible-use impact;
- migration or seed-reset impact;
- screenshots for material UI changes.

By contributing, you agree that your contribution is licensed under MIT-0.
