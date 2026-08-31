from __future__ import annotations

import struct
import xml.etree.ElementTree as ElementTree
from pathlib import Path

from scripts.build_site import HTML_FILES, render_static_html
from tools.repo_scan import RuntimeAssetParser

ROOT = Path(__file__).resolve().parents[1]
PACKAGE_WEB = ROOT / "src" / "marketplace_trust_starter" / "web"
SITE = ROOT / "site"

MIRRORED_ASSETS = (
    "assets/styles.css",
    "assets/landing.js",
    "assets/dashboard.js",
    "assets/architecture.js",
    "assets/demo-data.json",
    "assets/mark.svg",
    "assets/architecture.drawio",
    "assets/architecture.png",
    "assets/aws-services-reference.drawio",
    "assets/aws-services-reference.png",
)


def test_publishable_html_is_an_explicit_static_render() -> None:
    for relative_path in HTML_FILES:
        source = PACKAGE_WEB / relative_path
        published = SITE / relative_path
        source_text = source.read_text(encoding="utf-8")
        published_text = published.read_text(encoding="utf-8")

        assert '<meta name="mts-runtime" content="service">' in source_text
        assert '<meta name="mts-runtime" content="static">' in published_text
        assert published_text == render_static_html(source)


def test_non_html_public_assets_match_the_served_package() -> None:
    for relative_path in MIRRORED_ASSETS:
        assert (PACKAGE_WEB / relative_path).read_bytes() == (SITE / relative_path).read_bytes()


def test_static_site_has_no_remote_runtime_assets() -> None:
    for html_path in (
        SITE / "index.html",
        SITE / "dashboard.html",
        SITE / "architecture.html",
    ):
        parser = RuntimeAssetParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        remote_assets = [
            value
            for value, _line in parser.assets
            if value.startswith(("http://", "https://", "//"))
        ]
        assert remote_assets == []


def test_site_references_existing_local_assets() -> None:
    for html_path in (
        SITE / "index.html",
        SITE / "dashboard.html",
        SITE / "architecture.html",
    ):
        parser = RuntimeAssetParser()
        parser.feed(html_path.read_text(encoding="utf-8"))
        local_assets = [
            value.split("?", 1)[0].split("#", 1)[0]
            for value, _line in parser.assets
            if value.startswith("assets/")
        ]
        assert local_assets
        for asset in local_assets:
            assert (SITE / asset).is_file(), f"{html_path.name} references missing {asset}"


def test_architecture_sources_and_png_renders_are_valid() -> None:
    for stem in ("architecture", "aws-services-reference"):
        drawio_path = PACKAGE_WEB / "assets" / f"{stem}.drawio"
        png_path = PACKAGE_WEB / "assets" / f"{stem}.png"

        root = ElementTree.parse(drawio_path).getroot()
        assert root.tag == "mxfile"
        assert root.find(".//mxGraphModel") is not None

        data = png_path.read_bytes()
        assert data.startswith(b"\x89PNG\r\n\x1a\n")
        width, height = struct.unpack(">II", data[16:24])
        assert width >= 1200
        assert height >= 700


def test_architecture_page_offers_both_editable_and_rendered_downloads() -> None:
    html = (SITE / "architecture.html").read_text(encoding="utf-8")
    for filename in (
        "architecture.drawio",
        "architecture.png",
        "aws-services-reference.drawio",
        "aws-services-reference.png",
    ):
        assert f'href="assets/{filename}" download' in html
    assert html.count('class="architecture-artifact"') == 2
