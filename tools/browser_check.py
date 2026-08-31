#!/usr/bin/env python3
"""Exercise the exact public site in Chrome and reject prohibited requests."""

from __future__ import annotations

import argparse
import contextlib
import functools
import http.server
import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import websocket

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGES_BASE = "/marketplace-trust-starter/"
EXPECTED_ASSETS = (
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


class RecordingHandler(http.server.SimpleHTTPRequestHandler):
    requests: list[str] = []

    def log_message(self, _format: str, *_args: object) -> None:
        return

    def do_GET(self) -> None:
        type(self).requests.append(self.path)
        super().do_GET()


class DevTools:
    def __init__(self, url: str, expected_origin: str) -> None:
        self.socket = websocket.create_connection(
            url,
            timeout=5,
            origin=expected_origin,
        )
        self.next_id = 1
        self.requests: list[str] = []
        self.failed_requests: list[str] = []
        self.exceptions: list[str] = []

    def close(self) -> None:
        self.socket.close()

    def _record(self, message: dict[str, Any]) -> None:
        method = message.get("method")
        params = message.get("params", {})
        if method == "Network.requestWillBeSent":
            self.requests.append(params.get("request", {}).get("url", ""))
        elif method == "Network.loadingFailed":
            self.failed_requests.append(params.get("errorText", "request failed"))
        elif method == "Runtime.exceptionThrown":
            detail = params.get("exceptionDetails", {})
            self.exceptions.append(detail.get("text", "browser exception"))
        elif method == "Log.entryAdded":
            entry = params.get("entry", {})
            if entry.get("level") == "error":
                self.exceptions.append(entry.get("text", "browser log error"))

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        identifier = self.next_id
        self.next_id += 1
        self.socket.send(
            json.dumps({"id": identifier, "method": method, "params": params or {}})
        )
        while True:
            message = json.loads(self.socket.recv())
            self._record(message)
            if message.get("id") != identifier:
                continue
            if "error" in message:
                raise RuntimeError(f"{method}: {message['error']}")
            return message.get("result", {})

    def evaluate(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": True,
            },
        )
        value = result.get("result", {})
        if value.get("subtype") == "error":
            raise RuntimeError(value.get("description", expression))
        return value.get("value")

    def wait_for(self, expression: str, timeout: float = 10) -> Any:
        deadline = time.monotonic() + timeout
        last_value: Any = None
        while time.monotonic() < deadline:
            last_value = self.evaluate(expression)
            if last_value:
                return last_value
            time.sleep(0.1)
        raise AssertionError(f"browser condition timed out: {expression} ({last_value!r})")

    def navigate(self, url: str) -> None:
        self.call("Page.navigate", {"url": url})
        self.wait_for("document.readyState === 'complete'")


def locate_chrome() -> str:
    candidates = [
        os.getenv("CHROME_BIN", ""),
        shutil.which("google-chrome") or "",
        shutil.which("chromium") or "",
        shutil.which("chromium-browser") or "",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return candidate
    raise RuntimeError("Chrome or Chromium was not found")


def free_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


@contextlib.contextmanager
def local_site() -> Any:
    with tempfile.TemporaryDirectory(prefix="marketplace-trust-pages-") as directory:
        document_root = Path(directory)
        destination = document_root / PAGES_BASE.strip("/")
        shutil.copytree(SITE, destination)
        handler = functools.partial(RecordingHandler, directory=str(document_root))
        RecordingHandler.requests = []
        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield (
                f"http://127.0.0.1:{server.server_port}{PAGES_BASE}",
                RecordingHandler.requests,
            )
        finally:
            server.shutdown()
            thread.join(timeout=5)


@contextlib.contextmanager
def chrome_session() -> Any:
    with tempfile.TemporaryDirectory(
        prefix="marketplace-trust-chrome-",
        ignore_cleanup_errors=True,
    ) as directory:
        profile = Path(directory)
        port = free_port()
        command = [
            locate_chrome(),
            "--headless=new",
            "--disable-background-networking",
            "--disable-breakpad",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-features=MediaRouter,OptimizationHints",
            "--disable-gpu",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-first-run",
            "--no-sandbox",
            "--remote-allow-origins=*",
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile}",
            "about:blank",
        ]
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            endpoint = f"http://127.0.0.1:{port}/json/version"
            deadline = time.monotonic() + 15
            version: dict[str, Any] | None = None
            while time.monotonic() < deadline:
                try:
                    with urllib.request.urlopen(endpoint, timeout=1) as response:
                        version = json.loads(response.read())
                    break
                except OSError:
                    time.sleep(0.1)
            if version is None:
                raise RuntimeError("Chrome DevTools endpoint did not become ready")
            target_request = urllib.request.Request(
                f"http://127.0.0.1:{port}/json/new?"
                f"{urllib.parse.quote('about:blank')}",
                method="PUT",
            )
            with urllib.request.urlopen(target_request, timeout=5) as response:
                target = json.loads(response.read())
            tools = DevTools(
                target["webSocketDebuggerUrl"],
                f"http://127.0.0.1:{port}",
            )
            tools.call("Page.enable")
            tools.call("Runtime.enable")
            tools.call("Network.enable")
            tools.call("Log.enable")
            try:
                yield tools
            finally:
                tools.close()
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def verify_browser(base_url: str) -> dict[str, object]:
    origin = urllib.parse.urlsplit(base_url)
    allowed_origin = f"{origin.scheme}://{origin.netloc}"
    with chrome_session() as browser:
        browser.navigate(base_url)
        require(
            "Trust decisions people can"
            in browser.evaluate("document.querySelector('h1').textContent"),
            "landing page heading is missing",
        )
        require(
            browser.evaluate(
                "document.querySelector('meta[name=\"mts-runtime\"]').content"
            )
            == "static",
            "landing page is not in static publication mode",
        )

        browser.navigate(urllib.parse.urljoin(base_url, "architecture.html"))
        require(
            browser.wait_for("document.querySelectorAll('.architecture-tab').length") == 4,
            "architecture flow tabs did not render",
        )
        before = browser.evaluate("document.querySelector('#stepLabel').textContent")
        browser.evaluate("document.querySelector('#flowNext').click()")
        after = browser.wait_for(
            "document.querySelector('#stepLabel').textContent !== "
            + json.dumps(before)
            + " && document.querySelector('#stepLabel').textContent"
        )
        require(before != after, "architecture next-step interaction failed")
        require(
            browser.evaluate(
                "[...document.querySelectorAll('a[download]')].length"
            )
            >= 4,
            "architecture downloads are incomplete",
        )
        require(
            browser.evaluate(
                "[...document.querySelectorAll('img.architecture-artifact')]"
                ".every((image) => image.complete && image.naturalWidth > 0)"
            ),
            "architecture PNG did not load",
        )

        browser.navigate(urllib.parse.urljoin(base_url, "dashboard.html"))
        require(
            browser.wait_for(
                "document.querySelector('.environment-pill').textContent === "
                "'Static preview'"
            ),
            "dashboard did not enter static preview mode",
        )
        require(
            browser.wait_for(
                "document.querySelector('#kpiAssessments').textContent === '10'"
            ),
            "dashboard snapshot did not render",
        )
        browser.evaluate("document.querySelector('[data-view=\"cases\"]').click()")
        require(
            browser.evaluate(
                "document.querySelector('[data-view-panel=\"cases\"]').classList"
                ".contains('active')"
            ),
            "dashboard navigation interaction failed",
        )

        browser.call(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": 390,
                "height": 844,
                "deviceScaleFactor": 1,
                "mobile": True,
            },
        )
        browser.navigate(base_url)
        require(
            browser.evaluate(
                "document.documentElement.scrollWidth <= "
                "document.documentElement.clientWidth"
            ),
            "mobile landing page has horizontal overflow",
        )

        http_requests = [
            url for url in browser.requests if url.startswith(("http://", "https://"))
        ]
        external_requests = [
            url for url in http_requests if not url.startswith(allowed_origin)
        ]
        api_requests = [
            url
            for url in http_requests
            if "/api/" in urllib.parse.urlsplit(url).path
        ]
        require(not external_requests, f"external requests: {external_requests}")
        require(not api_requests, f"public site requested API routes: {api_requests}")
        require(not browser.failed_requests, f"failed requests: {browser.failed_requests}")
        require(not browser.exceptions, f"browser exceptions: {browser.exceptions}")
        return {
            "ok": True,
            "base_url": base_url,
            "page_count": 3,
            "interaction_count": 3,
            "mobile_width": 390,
            "request_count": len(http_requests),
            "external_request_count": len(external_requests),
            "api_request_count": len(api_requests),
            "browser_exception_count": len(browser.exceptions),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url")
    args = parser.parse_args()
    if args.base_url:
        result = verify_browser(args.base_url.rstrip("/") + "/")
    else:
        missing = [asset for asset in EXPECTED_ASSETS if not (SITE / asset).is_file()]
        require(not missing, f"missing site assets: {missing}")
        with local_site() as (base_url, _requests):
            result = verify_browser(base_url)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
