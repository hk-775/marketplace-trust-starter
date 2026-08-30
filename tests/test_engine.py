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


def test_profile_assessment_is_explainable_and_routes_critical_risk() -> None:
    result = assess_profile(
        ProfileAssessmentRequest(
            subject_id="profile-test-01",
            bio="Message me for a guaranteed return from crypto.",
            account_age_days=1,
            profile_completeness=0.4,
            outbound_messages_1h=40,
            unique_recipients_1h=20,
            bio_reuse_count_7d=9,
            linked_accounts_30d=8,
            prior_reports_30d=6,
        ),
        policies(),
        assessment_id="A-TEST-PROFILE",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )

    assert result.risk_tier is RiskTier.CRITICAL
    assert result.requires_human_review is True
    assert result.risk_score <= 100
    assert {signal.signal_id for signal in result.signals} >= {
        "profile_scam_language",
        "profile_reuse",
        "profile_linkage",
    }
    assert all(signal.evidence for signal in result.signals)
    assert result.recommended_action.startswith("prioritize_human_review")


def test_content_detects_credentials_without_hiding_point_math() -> None:
    result = assess_content(
        ContentAssessmentRequest(
            subject_id="content-test-01",
            content_id="message-test-01",
            content_type="message",
            text=(
                "Your account is suspended. Verify your account at "
                "http://verify.invalid and send the verification code."
            ),
            account_age_days=1,
            previous_similar_posts_1h=8,
            unique_recipients_1h=12,
        ),
        policies(),
        assessment_id="A-TEST-CONTENT",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )

    by_id = {signal.signal_id: signal for signal in result.signals}
    assert "content_credentials" in by_id
    assert "content_spam_repetition" in by_id
    assert by_id["content_credentials"].points == round(
        by_id["content_credentials"].base_points * by_id["content_credentials"].multiplier
    )
    assert result.risk_tier is RiskTier.HIGH
    assert result.requires_human_review is True


def test_coordinated_abuse_requires_correlated_signals() -> None:
    result = assess_coordination(
        CoordinatedAbuseRequest(
            cluster_id="cluster-test-01",
            participating_accounts=15,
            new_account_ratio=0.86,
            duplicate_content_ratio=0.9,
            shared_device_ratio=0.74,
            events_10m=190,
            target_concentration=0.8,
            independent_reports=8,
            established_account_ratio=0.05,
        ),
        policies(),
        assessment_id="A-TEST-COORD",
        created_at="2026-08-30T12:00:00Z",
        policy_version=1,
    )

    assert result.risk_score == 100
    assert result.risk_tier is RiskTier.CRITICAL
    assert {signal.signal_id for signal in result.signals} == {
        "coordination_similarity",
        "coordination_velocity",
        "coordination_targeting",
        "coordination_shared_infrastructure",
        "coordination_new_accounts",
    }


def test_policy_multiplier_changes_only_named_signal_contribution() -> None:
    configured = policies()
    configured["content_scam"]["weight"] = 0.5
    result = assess_content(
        ContentAssessmentRequest(
            subject_id="content-test-02",
            content_id="message-test-02",
            content_type="message",
            text="Buy a gift card and send the code.",
            account_age_days=90,
        ),
        configured,
        assessment_id="A-TEST-POLICY",
        created_at="2026-08-30T12:00:00Z",
        policy_version=2,
    )

    assert result.risk_score == 17
    assert result.signals[0].signal_id == "content_scam"
    assert result.signals[0].base_points == 34
    assert result.signals[0].multiplier == 0.5
    assert result.policy_version == 2
