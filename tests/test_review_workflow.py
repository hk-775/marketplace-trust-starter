from __future__ import annotations


def test_case_must_enter_review_before_resolution(client) -> None:
    response = client.patch(
        "/api/v1/cases/C-2002",
        json={
            "status": "resolved",
            "reviewer": "Jordan Lee",
            "outcome": "confirmed_abuse",
            "resolution_notes": "Confirmed after reviewing the evidence.",
        },
    )
    assert response.status_code == 409
    assert "must enter in_review" in response.json()["detail"]


def test_full_review_workflow_updates_state_and_audit(client) -> None:
    started = client.patch(
        "/api/v1/cases/C-2002",
        json={"status": "in_review", "reviewer": "Jordan Lee"},
    )
    assert started.status_code == 200
    assert started.json()["status"] == "in_review"
    assert started.json()["assigned_to"] == "Jordan Lee"
    assert started.json()["review_started_at"]

    resolved = client.patch(
        "/api/v1/cases/C-2002",
        json={
            "status": "resolved",
            "reviewer": "Jordan Lee",
            "outcome": "false_positive",
            "resolution_notes": "The payment request was part of an approved test listing.",
        },
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"
    assert resolved.json()["outcome"] == "false_positive"
    assert resolved.json()["resolved_at"]

    audit = client.get("/api/v1/audit?limit=250").json()
    case_events = [event["action"] for event in audit["items"] if event["entity_id"] == "C-2002"]
    assert "review_started" in case_events
    assert "case_resolved" in case_events
    assert audit["chain_valid"] is True


def test_resolved_case_is_terminal(client) -> None:
    response = client.patch(
        "/api/v1/cases/C-2006",
        json={"status": "in_review", "reviewer": "Jordan Lee"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "resolved cases are immutable"


def test_resolution_requires_meaningful_notes(client) -> None:
    client.patch(
        "/api/v1/cases/C-2002",
        json={"status": "in_review", "reviewer": "Jordan Lee"},
    )
    response = client.patch(
        "/api/v1/cases/C-2002",
        json={
            "status": "resolved",
            "reviewer": "Jordan Lee",
            "outcome": "no_action",
            "resolution_notes": "short",
        },
    )
    assert response.status_code == 422
