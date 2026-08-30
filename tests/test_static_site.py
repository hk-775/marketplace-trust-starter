from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_WEB = ROOT / "src" / "marketplace_trust_starter" / "web"
SITE = ROOT / "site"


def test_publishable_site_matches_served_landing_and_architecture() -> None:
    relative_paths = [
        "index.html",
        "dashboard.html",
        "architecture.html",
        "assets/styles.css",
        "assets/landing.js",
        "assets/dashboard.js",
        "assets/architecture.js",
        "assets/demo-data.json",
        "assets/mark.svg",
    ]
    for relative_path in relative_paths:
        assert (PACKAGE_WEB / relative_path).read_bytes() == (SITE / relative_path).read_bytes()


def test_static_site_has_no_remote_runtime_assets() -> None:
    for html_path in (
        SITE / "index.html",
        SITE / "dashboard.html",
        SITE / "architecture.html",
    ):
        html = html_path.read_text(encoding="utf-8")
        remote_sources = re.findall(
            r"""(?:src|href)=["']https?://[^"']+["']""",
            html,
            flags=re.IGNORECASE,
        )
        assert remote_sources == []


def test_site_references_existing_local_assets() -> None:
    for html_path in (
        SITE / "index.html",
        SITE / "dashboard.html",
        SITE / "architecture.html",
    ):
        html = html_path.read_text(encoding="utf-8")
        assets = re.findall(r"""(?:src|href)=["'](assets/[^"'?#]+)""", html)
        assert assets
        for asset in assets:
            assert (SITE / asset).is_file(), f"{html_path.name} references missing {asset}"
