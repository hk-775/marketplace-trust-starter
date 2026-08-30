#!/usr/bin/env python3
"""Live HTTP smoke test for the seeded demo on the canonical local port."""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request

DEFAULT_BASE_URL = "http://127.0.0.1:8101"


def request_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
    with urllib.request.urlopen(request, timeout=5) as response:
        return response.status, json.loads(response.read())


def wait_until_ready(base_url: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            status, payload = request_json(f"{base_url}/api/v1/health")
            if status == 200 and payload.get("status") == "ok":
                return
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
        time.sleep(0.25)
    raise AssertionError(f"service did not become ready at {base_url}: {last_error}")


def assert_page(base_url: str, path: str, expected_text: bytes) -> None:
    with urllib.request.urlopen(f"{base_url}{path}", timeout=5) as response:
        body = response.read()
        assert response.status == 200, (path, response.status)
        assert expected_text in body, path


def run(base_url: str) -> None:
    wait_until_ready(base_url, 20)
    status, health = request_json(f"{base_url}/api/v1/health")
    assert status == 200
    assert health["counts"]["assessments"] == 10
    assert health["ethical_boundaries"]["protected_attribute_inference"] == "prohibited"

    assert_page(base_url, "/", b"Trust decisions people can")
    assert_page(base_url, "/dashboard", b"Trust operations overview")
    assert_page(base_url, "/architecture", b"explicit decision boundaries")

    status, assessment = request_json(
        f"{base_url}/api/v1/assess/content",
        method="POST",
        payload={
            "subject_id": "smoke-local-seller",
            "content_id": "smoke-listing-001",
            "content_type": "listing",
            "text": "Wooden chair available for pickup Saturday.",
            "account_age_days": 400,
            "successful_transactions_90d": 12,
        },
    )
    assert status == 201
    assert assessment["risk_tier"] == "low"
    assert assessment["case_id"] is None

    status, audit = request_json(f"{base_url}/api/v1/audit")
    assert status == 200
    assert audit["chain_valid"] is True

    status, reset = request_json(
        f"{base_url}/api/v1/demo/reset",
        method="POST",
        payload={"actor": "smoke-test", "confirmation": "RESET DEMO"},
    )
    assert status == 200
    assert reset["assessments"] == 10
    print(f"Smoke test passed at {base_url}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    run(args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
