from __future__ import annotations


def test_locked_safety_boundary_cannot_be_changed(client) -> None:
    response = client.patch(
        "/api/v1/policies/protected_attribute_guard",
        json={
            "enabled": False,
            "actor": "Policy Tester",
            "reason": "Attempt to disable a locked rule",
        },
    )
    assert response.status_code == 409
    assert "locked safety boundary" in response.json()["detail"]


def test_policy_change_is_versioned_audited_and_affects_new_assessments(client) -> None:
    before = client.post(
        "/api/v1/assess/content",
        json={
            "subject_id": "policy-before-01",
            "content_id": "policy-message-before",
            "content_type": "message",
            "text": "Buy a gift card and send the code.",
            "account_age_days": 100,
        },
    ).json()
    assert before["risk_score"] == 34
    assert before["policy_version"] == 1

    updated = client.patch(
        "/api/v1/policies/content_scam",
        json={
            "enabled": False,
            "actor": "Policy Tester",
            "reason": "Demonstrate that policy changes affect only new assessments",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["enabled"] is False

    after = client.post(
        "/api/v1/assess/content",
        json={
            "subject_id": "policy-after-01",
            "content_id": "policy-message-after",
            "content_type": "message",
            "text": "Buy a gift card and send the code.",
            "account_age_days": 100,
        },
    ).json()
    assert after["risk_score"] == 0
    assert after["policy_version"] == 2

    assessments = client.get("/api/v1/assessments?limit=250").json()["items"]
    historical = next(
        item for item in assessments if item["assessment_id"] == before["assessment_id"]
    )
    assert historical["risk_score"] == 34
    assert historical["policy_version"] == 1

    audit = client.get("/api/v1/audit?limit=250").json()
    assert any(
        event["action"] == "policy_updated"
        and event["entity_id"] == "content_scam"
        and event["details"]["reason"].startswith("Demonstrate")
        for event in audit["items"]
    )
    assert audit["chain_valid"] is True


def test_reset_restores_canonical_seed_after_state_changes(client) -> None:
    client.post("/api/v1/demo/scenarios/coordinated-burst")
    client.patch(
        "/api/v1/policies/content_spam_burst",
        json={
            "weight": 0.5,
            "actor": "Reset Tester",
            "reason": "Create mutable state before reset",
        },
    )
    changed = client.get("/api/v1/health").json()["counts"]
    assert changed["assessments"] == 11
    assert changed["cases"] == 7

    response = client.post(
        "/api/v1/demo/reset",
        json={"actor": "Reset Tester", "confirmation": "RESET DEMO"},
    )
    assert response.status_code == 200
    assert response.json()["assessments"] == 10
    assert response.json()["cases"] == 6
    assert response.json()["policies"] == 28

    health = client.get("/api/v1/health").json()
    assert health["counts"]["assessments"] == 10
    assert health["counts"]["cases"] == 6
    assert client.get("/api/v1/metrics").json()["policy_version"] == 1
    assert client.get("/api/v1/audit").json()["chain_valid"] is True


def test_reset_requires_explicit_confirmation(client) -> None:
    response = client.post(
        "/api/v1/demo/reset",
        json={"actor": "Reset Tester", "confirmation": "yes"},
    )
    assert response.status_code == 422
