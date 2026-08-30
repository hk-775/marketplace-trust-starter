#!/usr/bin/env python3
"""Build or verify the publishable static mirror of all served web pages."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
PACKAGE_WEB = SRC / "marketplace_trust_starter" / "web"
SITE = ROOT / "site"
SNAPSHOT_TIME = "2026-08-30T14:00:00Z"
MIRRORED_FILES = (
    "index.html",
    "dashboard.html",
    "architecture.html",
    "assets/styles.css",
    "assets/landing.js",
    "assets/dashboard.js",
    "assets/architecture.js",
    "assets/demo-data.json",
    "assets/mark.svg",
)


def build_snapshot() -> str:
    sys.path.insert(0, str(SRC))
    import marketplace_trust_starter.store as store_module
    from marketplace_trust_starter.service import TrustSafetyService
    from marketplace_trust_starter.store import Store

    original_clock = store_module.utc_now
    store_module.utc_now = lambda: SNAPSHOT_TIME
    try:
        with tempfile.TemporaryDirectory() as temporary_directory:
            store = Store(Path(temporary_directory) / "static-demo.db")
            store.initialize()
            assessments, assessment_total = store.list_assessments(limit=250)
            cases, case_total = store.list_cases(limit=250)
            events, audit_total, chain_valid = store.audit_events(limit=250)
            snapshot = {
                "metrics": store.metrics(),
                "assessments": {
                    "items": [item.model_dump(mode="json") for item in assessments],
                    "total": assessment_total,
                },
                "cases": {
                    "items": [item.model_dump(mode="json") for item in cases],
                    "total": case_total,
                },
                "policies": [item.model_dump(mode="json") for item in store.list_policies()],
                "insights": store.insights(),
                "audit": {
                    "items": [item.model_dump(mode="json") for item in events],
                    "total": audit_total,
                    "chain_valid": chain_valid,
                },
                "scenarios": {"items": TrustSafetyService.demo_scenarios()},
            }
    finally:
        store_module.utc_now = original_clock
    return json.dumps(snapshot, indent=2, sort_keys=True) + "\n"


def write_build(snapshot: str) -> None:
    package_snapshot = PACKAGE_WEB / "assets" / "demo-data.json"
    package_snapshot.write_text(snapshot, encoding="utf-8")
    for relative_path in MIRRORED_FILES:
        source = PACKAGE_WEB / relative_path
        destination = SITE / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def verify_build(snapshot: str) -> list[str]:
    errors: list[str] = []
    package_snapshot = PACKAGE_WEB / "assets" / "demo-data.json"
    if not package_snapshot.exists() or package_snapshot.read_text(encoding="utf-8") != snapshot:
        errors.append("package static demo snapshot is stale")
    for relative_path in MIRRORED_FILES:
        source = PACKAGE_WEB / relative_path
        destination = SITE / relative_path
        if not source.is_file():
            errors.append(f"missing served asset: {relative_path}")
        elif not destination.is_file():
            errors.append(f"missing static mirror: {relative_path}")
        elif source.read_bytes() != destination.read_bytes():
            errors.append(f"static mirror differs: {relative_path}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify that the checked-in static mirror is current",
    )
    args = parser.parse_args()
    snapshot = build_snapshot()
    if args.check:
        errors = verify_build(snapshot)
        if errors:
            for error in errors:
                print(f"ERROR: {error}")
            return 1
        print("Static site mirror is current.")
        return 0
    write_build(snapshot)
    print(f"Built static site mirror in {SITE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
