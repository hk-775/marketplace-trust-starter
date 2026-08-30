from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from marketplace_trust_starter.app import create_app


def test_health_and_seeded_metrics_are_consistent(client) -> None:
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "ok"
    assert body["counts"] == {
        "assessments": 10,
        "cases": 6,
        "policies": 28,
        "audit_events": 23,
    }
    assert body["external_network_calls"] is False
    assert body["ethical_boundaries"]["face_or_attractiveness_scoring"] == "prohibited"

    metrics = client.get("/api/v1/metrics").json()
    assert metrics["kpis"]["total_assessments"] == 10
    assert metrics["kpis"]["review_queue"] == 4
    assert metrics["policy_version"] == 1


def test_high_risk_content_creates_a_real_review_case(client) -> None:
    response = client.post(
        "/api/v1/assess/content",
        json={
            "subject_id": "api-scam-01",
            "content_id": "api-message-01",
            "content_type": "message",
            "text": "Contact me on Telegram, buy a gift card, and send the code.",
            "account_age_days": 1,
            "previous_similar_posts_1h": 8,
            "unique_recipients_1h": 15,
            "reports_24h": 4,
        },
    )
    assert response.status_code == 201
    assessment = response.json()
    assert assessment["requires_human_review"] is True
    assert assessment["case_id"]

    case = client.get(f"/api/v1/cases/{assessment['case_id']}")
    assert case.status_code == 200
    case_body = case.json()
    assert case_body["status"] == "open"
    assert case_body["human_decision_required"] is True
    assert case_body["assessment_id"] == assessment["assessment_id"]
    assert case_body["evidence"] == assessment["signals"]


def test_low_risk_content_does_not_create_a_case(client) -> None:
    before = client.get("/api/v1/cases").json()["total"]
    response = client.post(
        "/api/v1/assess/content",
        json={
            "subject_id": "api-benign-01",
            "content_id": "api-listing-01",
            "content_type": "listing",
            "text": "Bookshelf available for local pickup this weekend.",
            "account_age_days": 400,
            "successful_transactions_90d": 12,
        },
    )
    assert response.status_code == 201
    assert response.json()["case_id"] is None
    assert client.get("/api/v1/cases").json()["total"] == before


def test_unknown_fields_are_rejected(client) -> None:
    response = client.post(
        "/api/v1/assess/content",
        json={
            "subject_id": "api-extra-01",
            "content_id": "api-extra-message",
            "content_type": "message",
            "text": "Hello",
            "unreviewed_magic_score": 0.9,
        },
    )
    assert response.status_code == 422


def test_two_app_instances_have_isolated_state(tmp_path: Path) -> None:
    first = TestClient(create_app(tmp_path / "first.db"))
    second = TestClient(create_app(tmp_path / "second.db"))
    first.post("/api/v1/demo/scenarios/gift-card-scam")

    assert first.get("/api/v1/health").json()["counts"]["assessments"] == 11
    assert second.get("/api/v1/health").json()["counts"]["assessments"] == 10


def test_web_pages_and_openapi_are_served(client) -> None:
    for path in (
        "/",
        "/index.html",
        "/dashboard",
        "/dashboard.html",
        "/architecture",
        "/architecture.html",
        "/api/openapi.json",
    ):
        assert client.get(path).status_code == 200
