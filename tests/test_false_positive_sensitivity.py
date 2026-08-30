from __future__ import annotations

from marketplace_trust_starter.engine import (
    assess_content,
    assess_coordination,
    assess_profile,
)
from marketplace_trust_starter.models import (
    ContentAssessmentRequest,
    CoordinatedAbuseRequest,
    ProfileAssessmentRequest,
    RiskTier,
)
from marketplace_trust_starter.seed import default_policy_rows


def policies() -> dict[str, dict]:
    return {row["policy_id"]: row for row in default_policy_rows()}


def test_link_alone_is_not_malicious() -> None:
    result = assess_content(
        ContentAssessmentRequest(
            subject_id="benign-link-01",
            content_id="listing-link-01",
            content_type="listing",
            text="Full dimensions are available at https://example.invalid/table.",
            account_age_days=200,
        ),
        policies(),
        assessment_id="A-BENIGN-LINK",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )
    assert result.risk_score == 0
    assert result.risk_tier is RiskTier.LOW
    assert result.signals == []


def test_safety_warning_suppresses_scam_and_credential_patterns() -> None:
    result = assess_content(
        ContentAssessmentRequest(
            subject_id="safety-educator-01",
            content_id="post-safety-01",
            content_type="post",
            text=(
                "Scam awareness: do not send gift cards, and never share your password "
                "or a verification code."
            ),
            account_age_days=500,
        ),
        policies(),
        assessment_id="A-SAFETY-WARNING",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )
    assert result.risk_score == 0
    assert result.signals == []


def test_ordinary_technical_phrase_is_not_a_targeted_threat() -> None:
    result = assess_content(
        ContentAssessmentRequest(
            subject_id="developer-01",
            content_id="comment-tech-01",
            content_type="comment",
            text="Please kill the process, then restart the worker.",
            account_age_days=300,
        ),
        policies(),
        assessment_id="A-TECH-PHRASE",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )
    assert "content_threat" not in {signal.signal_id for signal in result.signals}
    assert result.risk_tier is RiskTier.LOW


def test_sparse_new_profile_alone_stays_below_review() -> None:
    result = assess_profile(
        ProfileAssessmentRequest(
            subject_id="new-profile-01",
            bio="New here.",
            account_age_days=1,
            profile_completeness=0.2,
            verified_contact=True,
            media_count=1,
            outbound_messages_1h=2,
            unique_recipients_1h=2,
        ),
        policies(),
        assessment_id="A-SPARSE",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )
    assert result.risk_score == 7
    assert result.risk_tier is RiskTier.LOW
    assert result.requires_human_review is False


def test_shared_device_context_never_triggers_coordination_by_itself() -> None:
    result = assess_coordination(
        CoordinatedAbuseRequest(
            cluster_id="household-cluster-01",
            participating_accounts=5,
            new_account_ratio=0.1,
            duplicate_content_ratio=0.1,
            shared_device_ratio=0.95,
            events_10m=4,
            target_concentration=0.1,
            independent_reports=0,
            established_account_ratio=0.9,
        ),
        policies(),
        assessment_id="A-HOUSEHOLD",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )
    assert "coordination_shared_infrastructure" not in {
        signal.signal_id for signal in result.signals
    }
    assert result.risk_score == 0
    assert result.risk_tier is RiskTier.LOW


def test_api_rejects_protected_attribute_and_appearance_fields(client) -> None:
    base_payload = {
        "subject_id": "blocked-input-01",
        "bio": "Hello",
        "account_age_days": 2,
        "profile_completeness": 0.5,
    }
    for prohibited in (
        {"race": "not accepted"},
        {"attractiveness_score": 0.9},
        {"face_embedding": [0.1, 0.2]},
    ):
        response = client.post(
            "/api/v1/assess/profile",
            json={**base_payload, **prohibited},
        )
        assert response.status_code == 422
        assert "prohibited" in str(response.json()).lower()
