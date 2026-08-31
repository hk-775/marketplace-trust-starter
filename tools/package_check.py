#!/usr/bin/env python3
"""Build and inspect temporary source and wheel archives without publishing."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="marketplace-trust-package-") as directory:
        temporary_root = Path(directory)
        source_directory = temporary_root / "source"
        shutil.copytree(
            ROOT,
            source_directory,
            ignore=shutil.ignore_patterns(
                ".git",
                ".coverage",
                ".pytest_cache",
                ".ruff_cache",
                ".venv",
                "*.egg-info",
                "__pycache__",
                "*.pyc",
                "build",
                "dist",
            ),
        )
        output_directory = temporary_root / "dist"
        (temporary_root / "tmp").mkdir()
        command = [
            sys.executable,
            "-m",
            "build",
            "--no-isolation",
            "--outdir",
            str(output_directory),
            str(source_directory),
        ]
        completed = subprocess.run(
            command,
            cwd=source_directory,
            env={**os.environ, "TMPDIR": str(temporary_root / "tmp")},
            check=False,
            capture_output=True,
            text=True,
        )
        archives = sorted(output_directory.glob("*")) if output_directory.exists() else []
        wheel_members: list[str] = []
        source_members: list[str] = []
        for archive in archives:
            if archive.suffix == ".whl":
                with zipfile.ZipFile(archive) as package:
                    wheel_members = sorted(package.namelist())
            elif archive.name.endswith(".tar.gz"):
                with tarfile.open(archive, "r:gz") as package:
                    source_members = sorted(package.getnames())

        required_wheel_suffixes = {
            "marketplace_trust_starter/__init__.py",
            "marketplace_trust_starter/app.py",
            "marketplace_trust_starter/engine.py",
            "marketplace_trust_starter/store.py",
            "marketplace_trust_starter/web/assets/architecture.drawio",
            "marketplace_trust_starter/web/assets/architecture.png",
            "marketplace_trust_starter/web/assets/aws-services-reference.drawio",
            "marketplace_trust_starter/web/assets/aws-services-reference.png",
            "marketplace_trust_starter/web/index.html",
        }
        required_source_suffixes = {
            "/.github/workflows/ci.yml",
            "/.github/workflows/pages.yml",
            "/README.md",
            "/docs/ARCHITECTURE.md",
            "/docs/PRODUCTION_READINESS.md",
            "/docs/PUBLICATION_ARTIFACTS.md",
            "/site/assets/architecture.drawio",
            "/site/assets/architecture.png",
            "/site/assets/aws-services-reference.drawio",
            "/site/assets/aws-services-reference.png",
            "/site/architecture.html",
            "/tools/browser_check.py",
            "/tools/history_scan.py",
            "/tools/repo_scan.py",
            "/uv.lock",
        }
        wheel_ok = all(
            any(member.endswith(suffix) for member in wheel_members)
            for suffix in required_wheel_suffixes
        )
        source_ok = all(
            any(member.endswith(suffix) for member in source_members)
            for suffix in required_source_suffixes
        )
        result = {
            "ok": (
                completed.returncode == 0
                and len(archives) == 2
                and wheel_ok
                and source_ok
            ),
            "returncode": completed.returncode,
            "archive_count": len(archives),
            "archive_names": [archive.name for archive in archives],
            "wheel_member_count": len(wheel_members),
            "source_member_count": len(source_members),
            "wheel_contents_ok": wheel_ok,
            "source_contents_ok": source_ok,
            "artifacts": [
                {
                    "name": archive.name,
                    "bytes": archive.stat().st_size,
                    "sha256": sha256(archive),
                }
                for archive in archives
            ],
            "output_tail": (
                completed.stdout.splitlines() + completed.stderr.splitlines()
            )[-12:],
        }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
