#!/usr/bin/env python3
"""Dependency-free repository publication and safety checks."""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
import tomllib
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXCLUDED_PARTS = {
    ".coverage",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}

TEXT_SUFFIXES = {
    ".css",
    ".drawio",
    ".html",
    ".js",
    ".json",
    ".lock",
    ".md",
    ".py",
    ".svg",
    ".toml",
    ".txt",
    ".yml",
    ".yaml",
}

REQUIRED_FILES = {
    ".github/ISSUE_TEMPLATE/bug.yml",
    ".github/ISSUE_TEMPLATE/config.yml",
    ".github/ISSUE_TEMPLATE/question.yml",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
    ".github/workflows/pages.yml",
    ".gitignore",
    "CHANGELOG.md",
    "CODE_OF_CONDUCT.md",
    "CONTRIBUTING.md",
    "Dockerfile",
    "LICENSE",
    "MANIFEST.in",
    "NOTICE",
    "QUICKSTART.md",
    "README.md",
    "SECURITY.md",
    "SUPPORT.md",
    "docs/ARCHITECTURE.md",
    "docs/DEPLOYMENT.md",
    "docs/ETHICS.md",
    "docs/PRODUCTION_READINESS.md",
    "docs/PUBLICATION_ARTIFACTS.md",
    "docs/RELEASE_CHECKLIST.md",
    "pyproject.toml",
    "site/architecture.html",
    "site/assets/architecture.drawio",
    "site/assets/architecture.png",
    "site/assets/aws-services-reference.drawio",
    "site/assets/aws-services-reference.png",
    "site/dashboard.html",
    "site/index.html",
    "tools/browser_check.py",
    "tools/history_scan.py",
    "tools/package_check.py",
    "tools/repo_scan.py",
    "uv.lock",
}

CREDENTIAL_PATTERNS = (
    (
        "cloud access key identifier",
        re.compile(r"\b(?:" + "AK" + r"IA|" + "AS" + r"IA)[A-Z0-9]{16}\b"),
    ),
    (
        "GitHub token",
        re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    ),
    (
        "private key",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ),
    (
        "AWS account identifier in ARN",
        re.compile(r"\barn:(?:aws|aws-us-gov|aws-cn):[^:\s]+:[^:\s]*:\d{12}:"),
    ),
)


@dataclass(frozen=True, slots=True)
class Finding:
    scan: str
    path: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "scan": self.scan,
            "path": self.path,
            "message": self.message,
        }
        if self.line is not None:
            result["line"] = self.line
        return result


def _relative(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def _is_excluded(path: Path, root: Path = ROOT) -> bool:
    relative = path.relative_to(root)
    return any(
        part in EXCLUDED_PARTS or part.endswith(".egg-info")
        for part in relative.parts
    )


def source_files(root: Path = ROOT) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or _is_excluded(path, root):
            continue
        yield path


def text_files(root: Path = ROOT) -> Iterable[Path]:
    for path in source_files(root):
        if not path.suffix or path.suffix.casefold() in TEXT_SUFFIXES:
            yield path


def scan_required_files(root: Path = ROOT) -> list[Finding]:
    return [
        Finding("required_files", path, "required publication file is missing")
        for path in sorted(REQUIRED_FILES)
        if not (root / path).is_file()
    ]


def scan_python_syntax(root: Path = ROOT) -> list[Finding]:
    findings = []
    for path in source_files(root):
        if path.suffix != ".py":
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError) as error:
            findings.append(Finding("python_syntax", _relative(path, root), str(error)))
    return findings


def scan_formatting(root: Path = ROOT) -> list[Finding]:
    findings = []
    for path in text_files(root):
        try:
            data = path.read_bytes()
            text = data.decode("utf-8")
        except (OSError, UnicodeError) as error:
            findings.append(Finding("formatting", _relative(path, root), str(error)))
            continue
        if b"\r\n" in data:
            findings.append(
                Finding("formatting", _relative(path, root), "CRLF line endings")
            )
        if data and not data.endswith(b"\n"):
            findings.append(
                Finding("formatting", _relative(path, root), "missing final newline")
            )
        for line_number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip(" \t") != line:
                findings.append(
                    Finding(
                        "formatting",
                        _relative(path, root),
                        "trailing whitespace",
                        line_number,
                    )
                )
    return findings


def scan_structured_files(root: Path = ROOT) -> list[Finding]:
    findings = []
    for path in source_files(root):
        try:
            if path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
            elif path.suffix == ".toml" or path.name == "uv.lock":
                tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError, tomllib.TOMLDecodeError) as error:
            findings.append(
                Finding("structured_files", _relative(path, root), str(error))
            )
    return findings


def scan_credentials(root: Path = ROOT) -> list[Finding]:
    findings = []
    for path in text_files(root):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        for label, pattern in CREDENTIAL_PATTERNS:
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        "credentials",
                        _relative(path, root),
                        label,
                        text.count("\n", 0, match.start()) + 1,
                    )
                )
    return findings


class RuntimeAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[tuple[str, int]] = []

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        value: str | None = None
        if tag in {"script", "img", "audio", "video", "source"}:
            value = attributes.get("src")
        elif tag == "link":
            rel = (attributes.get("rel") or "").casefold()
            if rel in {"stylesheet", "icon", "preload", "modulepreload"}:
                value = attributes.get("href")
        if value:
            self.assets.append((value, self.getpos()[0]))


def scan_external_assets(root: Path = ROOT) -> list[Finding]:
    findings = []
    for path in sorted((root / "site").rglob("*.html")):
        parser = RuntimeAssetParser()
        parser.feed(path.read_text(encoding="utf-8"))
        for value, line in parser.assets:
            if value.startswith(("http://", "https://", "//")):
                findings.append(
                    Finding(
                        "external_assets",
                        _relative(path, root),
                        f"remote runtime asset: {value}",
                        line,
                    )
                )
    for path in sorted((root / "site").rglob("*")):
        if path.suffix not in {".css", ".js"}:
            continue
        text = path.read_text(encoding="utf-8")
        patterns = (
            re.compile(r"url\(\s*[\"']?https?://", re.IGNORECASE),
            re.compile(r"\b(?:fetch|WebSocket|EventSource)\(\s*[\"']https?://"),
        )
        for pattern in patterns:
            for match in pattern.finditer(text):
                findings.append(
                    Finding(
                        "external_assets",
                        _relative(path, root),
                        "remote runtime request",
                        text.count("\n", 0, match.start()) + 1,
                    )
                )
    return findings


def scan_workflows(root: Path = ROOT) -> list[Finding]:
    findings = []
    workflow_root = root / ".github" / "workflows"
    action_pattern = re.compile(r"^\s*uses:\s*([^@\s]+)@([^\s#]+)", re.MULTILINE)
    for path in sorted(workflow_root.glob("*.y*ml")):
        text = path.read_text(encoding="utf-8")
        if "pull_request_target:" in text:
            findings.append(
                Finding(
                    "workflows",
                    _relative(path, root),
                    "pull_request_target executes with elevated repository context",
                )
            )
        if re.search(r"runs-on:\s*(?:\[.*)?self-hosted", text, re.IGNORECASE):
            findings.append(
                Finding(
                    "workflows",
                    _relative(path, root),
                    "public workflow uses a self-hosted runner",
                )
            )
        if not re.search(r"^permissions:\s*$", text, re.MULTILINE):
            findings.append(
                Finding(
                    "workflows",
                    _relative(path, root),
                    "workflow has no explicit top-level permissions",
                )
            )
        for match in action_pattern.finditer(text):
            action, revision = match.groups()
            if action.startswith("./"):
                continue
            if not re.fullmatch(r"[0-9a-f]{40}", revision):
                findings.append(
                    Finding(
                        "workflows",
                        _relative(path, root),
                        f"action is not pinned to a full commit: {action}@{revision}",
                        text.count("\n", 0, match.start()) + 1,
                    )
                )
    return findings


def scan_publication_mode(root: Path = ROOT) -> list[Finding]:
    findings = []
    source_root = root / "src" / "marketplace_trust_starter" / "web"
    for name in ("index.html", "dashboard.html", "architecture.html"):
        source = (source_root / name).read_text(encoding="utf-8")
        published = (root / "site" / name).read_text(encoding="utf-8")
        if '<meta name="mts-runtime" content="service">' not in source:
            findings.append(
                Finding("publication_mode", f"src/.../web/{name}", "service marker missing")
            )
        if '<meta name="mts-runtime" content="static">' not in published:
            findings.append(
                Finding("publication_mode", f"site/{name}", "static marker missing")
            )
    return findings


def scan_packaging(root: Path = ROOT) -> list[Finding]:
    findings = []
    if not (root / "uv.lock").is_file():
        findings.append(Finding("packaging", "uv.lock", "locked environment missing"))
    for path in source_files(root):
        if path.suffix == ".whl" or path.name.endswith((".tar.gz", ".zip")):
            findings.append(
                Finding(
                    "packaging",
                    _relative(path, root),
                    "generated distribution archive is committed",
                )
            )
        if path.is_symlink():
            findings.append(
                Finding("packaging", _relative(path, root), "symlink is not publishable")
            )
    return findings


SCANS: dict[str, Callable[[Path], list[Finding]]] = {
    "required_files": scan_required_files,
    "python_syntax": scan_python_syntax,
    "formatting": scan_formatting,
    "structured_files": scan_structured_files,
    "credentials": scan_credentials,
    "external_assets": scan_external_assets,
    "workflows": scan_workflows,
    "publication_mode": scan_publication_mode,
    "packaging": scan_packaging,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scans", nargs="*", choices=sorted(SCANS))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    selected = args.scans or list(SCANS)
    results: dict[str, object] = {}
    findings: list[Finding] = []
    for name in selected:
        scan_findings = SCANS[name](args.root.resolve())
        findings.extend(scan_findings)
        results[name] = {
            "ok": not scan_findings,
            "finding_count": len(scan_findings),
        }
    result = {
        "ok": not findings,
        "scan_count": len(selected),
        "finding_count": len(findings),
        "scans": results,
        "findings": [finding.to_dict() for finding in findings],
    }
    json.dump(
        result,
        sys.stdout,
        indent=2 if args.pretty else None,
        sort_keys=True,
        separators=None if args.pretty else (",", ":"),
    )
    sys.stdout.write("\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
