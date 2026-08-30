"""Deterministic fictional demo data and default policy controls."""

from __future__ import annotations

from typing import Any

from marketplace_trust_starter.engine import (
    assess_content,
    assess_coordination,
    assess_profile,
)
from marketplace_trust_starter.models import (
    AssessmentResponse,
    CaseStatus,
    ContentAssessmentRequest,
    CoordinatedAbuseRequest,
    ProfileAssessmentRequest,
    ReviewCase,
    ReviewOutcome,
)

SEED_DATE = "2026-08-30"
SEED_POLICY_VERSION = 1


def default_policy_rows() -> list[dict[str, Any]]:
    updated_at = f"{SEED_DATE}T13:00:00Z"
    rows = [
        (
            "profile_completeness",
            "Sparse new profile",
            "Scores low completeness only for a newly created account.",
            "profile",
            True,
            1.0,
            0.35,
            True,
        ),
        (
            "profile_velocity",
            "New-account outreach burst",
            "Requires both a new account and broad one-hour recipient activity.",
            "behavior",
            True,
            1.0,
            24,
            True,
        ),
        (
            "profile_reuse",
            "Repeated profile text",
            "Detects repeated profile text across recent accounts.",
            "coordination",
            True,
            1.0,
            5,
            True,
        ),
        (
            "profile_scam_language",
            "Profile financial solicitation",
            "Requires a payment instrument plus requested action or guaranteed-return claim.",
            "content",
            True,
            1.0,
            1,
            True,
        ),
        (
            "profile_report_history",
            "Profile report context",
            "Adds capped supporting context from recent independent reports.",
            "reports",
            True,
            1.0,
            3,
            True,
        ),
        (
            "profile_payment_abuse",
            "Payment reversal pattern",
            "Detects multiple recent chargebacks.",
            "transactions",
            True,
            1.0,
            2,
            True,
        ),
        (
            "profile_linkage",
            "Linked-account reuse",
            "Counts account linkage only when content reuse also exists.",
            "coordination",
            True,
            1.0,
            4,
            True,
        ),
        (
            "verified_contact_counter",
            "Verified contact counter-signal",
            "Modestly reduces uncertainty for a verified contact channel.",
            "counter_signal",
            True,
            1.0,
            1,
            True,
        ),
        (
            "established_history_counter",
            "Established history counter-signal",
            "Rewards sustained successful activity without reports or chargebacks.",
            "counter_signal",
            True,
            1.0,
            180,
            True,
        ),
        (
            "complete_profile_counter",
            "Complete profile counter-signal",
            "Modestly reduces uncertainty for a substantive profile.",
            "counter_signal",
            True,
            1.0,
            0.8,
            True,
        ),
        (
            "content_scam",
            "Payment or investment solicitation",
            "Requires both a financial instrument and a requested action.",
            "content",
            True,
            1.0,
            1,
            True,
        ),
        (
            "content_credentials",
            "Credential-harvesting pattern",
            "Requires account-verification context plus a secret or login prompt.",
            "content",
            True,
            1.0,
            1,
            True,
        ),
        (
            "content_threat",
            "Direct targeted threat",
            "Uses a narrow set of direct threat patterns to protect precision.",
            "content",
            True,
            1.0,
            1,
            True,
        ),
        (
            "content_spam_repetition",
            "Repeated content distribution",
            "Requires similar content and multiple distinct recipients.",
            "spam",
            True,
            1.0,
            5,
            True,
        ),
        (
            "content_spam_burst",
            "New-account distribution burst",
            "Detects broad distribution by a recently created account.",
            "spam",
            True,
            1.0,
            25,
            True,
        ),
        (
            "content_off_platform",
            "Risk-context off-platform move",
            "Counts off-platform solicitation only with new-account or scam context.",
            "scam",
            True,
            1.0,
            1,
            True,
        ),
        (
            "content_report_history",
            "Content report context",
            "Adds capped supporting context from recent independent reports.",
            "reports",
            True,
            1.0,
            3,
            True,
        ),
        (
            "content_history_counter",
            "Positive transaction history",
            "Modestly reduces uncertainty for established successful activity.",
            "counter_signal",
            True,
            1.0,
            365,
            True,
        ),
        (
            "coordination_similarity",
            "Cross-account content similarity",
            "Requires substantial duplication across at least four accounts.",
            "coordination",
            True,
            1.0,
            0.72,
            True,
        ),
        (
            "coordination_velocity",
            "Synchronized activity burst",
            "Detects high event velocity across at least five accounts.",
            "coordination",
            True,
            1.0,
            80,
            True,
        ),
        (
            "coordination_targeting",
            "Concentrated target pressure",
            "Requires target concentration plus independent reports.",
            "coordination",
            True,
            1.0,
            0.65,
            True,
        ),
        (
            "coordination_shared_infrastructure",
            "Shared infrastructure corroboration",
            "Never scores alone; it corroborates similarity or velocity evidence.",
            "coordination",
            True,
            1.0,
            0.6,
            True,
        ),
        (
            "coordination_new_accounts",
            "New-account cluster",
            "Requires a mostly new-account cluster plus duplicated content.",
            "coordination",
            True,
            1.0,
            0.7,
            True,
        ),
        (
            "coordination_history_counter",
            "Established cluster counter-signal",
            "Reduces concern for established accounts with diverse content and no reports.",
            "counter_signal",
            True,
            1.0,
            0.7,
            True,
        ),
        (
            "risk_guarded_threshold",
            "Guarded tier threshold",
            "Score where enhanced observation begins.",
            "governance",
            True,
            1.0,
            25,
            False,
        ),
        (
            "human_review_gate",
            "Human review gate",
            "Scores at or above this value create a real review case; never an automatic ban.",
            "governance",
            True,
            1.0,
            50,
            False,
        ),
        (
            "risk_critical_threshold",
            "Critical tier threshold",
            "Score where human review receives urgent priority.",
            "governance",
            True,
            1.0,
            75,
            False,
        ),
        (
            "protected_attribute_guard",
            "Protected-attribute and appearance guard",
            "Rejects protected-attribute, biometric, face, and attractiveness inputs.",
            "ethical_boundary",
            True,
            1.0,
            1,
            False,
        ),
    ]
    return [
        {
            "policy_id": policy_id,
            "name": name,
            "description": description,
            "category": category,
            "enabled": enabled,
            "weight": weight,
            "threshold": threshold,
            "default_enabled": enabled,
            "default_weight": weight,
            "default_threshold": threshold,
            "editable": editable,
            "version": 1,
            "updated_at": updated_at,
        }
        for (
            policy_id,
            name,
            description,
            category,
            enabled,
            weight,
            threshold,
            editable,
        ) in rows
    ]


def _policy_map(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {row["policy_id"]: row for row in rows}


def build_seed_assessments(
    policy_rows: list[dict[str, Any]],
) -> list[AssessmentResponse]:
    policies = _policy_map(policy_rows)
    profile_inputs = [
        (
            "A-1001",
            "2026-08-30T13:12:00Z",
            ProfileAssessmentRequest(
                subject_id="cedar-otter-104",
                bio="Neighborhood ceramicist. Pickup available at the weekend market.",
                account_age_days=740,
                profile_completeness=0.94,
                verified_contact=True,
                media_count=6,
                successful_transactions_90d=18,
            ),
        ),
        (
            "A-1005",
            "2026-08-30T13:26:00Z",
            ProfileAssessmentRequest(
                subject_id="silver-lantern-772",
                bio="Message me on Telegram for a guaranteed crypto return.",
                account_age_days=2,
                profile_completeness=0.45,
                outbound_messages_1h=31,
                unique_recipients_1h=14,
                bio_reuse_count_7d=8,
                linked_accounts_30d=7,
                prior_reports_30d=5,
            ),
        ),
        (
            "A-1007",
            "2026-08-30T13:34:00Z",
            ProfileAssessmentRequest(
                subject_id="paper-kite-288",
                bio="New here.",
                account_age_days=1,
                profile_completeness=0.22,
                verified_contact=True,
                media_count=1,
                outbound_messages_1h=3,
                unique_recipients_1h=2,
            ),
        ),
    ]
    content_inputs = [
        (
            "A-1002",
            "2026-08-30T13:16:00Z",
            ContentAssessmentRequest(
                subject_id="silver-lantern-772",
                content_id="msg-4412",
                content_type="message",
                text="Message me on Telegram. Buy a gift card and send the code today.",
                account_age_days=2,
                previous_similar_posts_1h=2,
                unique_recipients_1h=7,
                reports_24h=4,
            ),
        ),
        (
            "A-1004",
            "2026-08-30T13:22:00Z",
            ContentAssessmentRequest(
                subject_id="copper-sparrow-551",
                content_id="listing-913",
                content_type="listing",
                text="Weekend desk sale. Pickup only; details are in the listing.",
                account_age_days=3,
                previous_similar_posts_1h=11,
                unique_recipients_1h=31,
                reports_24h=0,
            ),
        ),
        (
            "A-1006",
            "2026-08-30T13:30:00Z",
            ContentAssessmentRequest(
                subject_id="storm-glass-019",
                content_id="comment-118",
                content_type="comment",
                text="I will find where you live and you will regret this.",
                account_age_days=88,
                previous_similar_posts_1h=0,
                unique_recipients_1h=1,
                reports_24h=4,
            ),
        ),
        (
            "A-1008",
            "2026-08-30T13:38:00Z",
            ContentAssessmentRequest(
                subject_id="cedar-otter-104",
                content_id="listing-922",
                content_type="listing",
                text="Handmade blue mugs, set of four. Local pickup Saturday afternoon.",
                account_age_days=740,
                previous_similar_posts_1h=0,
                unique_recipients_1h=1,
                reports_24h=0,
                successful_transactions_90d=18,
            ),
        ),
        (
            "A-1010",
            "2026-08-30T13:46:00Z",
            ContentAssessmentRequest(
                subject_id="violet-bridge-430",
                content_id="msg-4470",
                content_type="message",
                text="Your account is suspended. Verify your account at http://verify.invalid "
                "and send the verification code.",
                account_age_days=1,
                previous_similar_posts_1h=9,
                unique_recipients_1h=12,
                reports_24h=2,
            ),
        ),
    ]
    coordination_inputs = [
        (
            "A-1003",
            "2026-08-30T13:19:00Z",
            CoordinatedAbuseRequest(
                cluster_id="cluster-northstar",
                participating_accounts=19,
                new_account_ratio=0.84,
                duplicate_content_ratio=0.91,
                shared_device_ratio=0.72,
                events_10m=186,
                target_concentration=0.78,
                independent_reports=9,
                established_account_ratio=0.08,
            ),
        ),
        (
            "A-1009",
            "2026-08-30T13:42:00Z",
            CoordinatedAbuseRequest(
                cluster_id="cluster-workshop",
                participating_accounts=8,
                new_account_ratio=0.1,
                duplicate_content_ratio=0.82,
                shared_device_ratio=0.75,
                events_10m=95,
                target_concentration=0.12,
                independent_reports=0,
                established_account_ratio=0.9,
            ),
        ),
    ]

    assessments: list[AssessmentResponse] = []
    for assessment_id, created_at, request in profile_inputs:
        assessments.append(
            assess_profile(
                request,
                policies,
                assessment_id=assessment_id,
                created_at=created_at,
                policy_version=SEED_POLICY_VERSION,
            )
        )
    for assessment_id, created_at, request in content_inputs:
        assessments.append(
            assess_content(
                request,
                policies,
                assessment_id=assessment_id,
                created_at=created_at,
                policy_version=SEED_POLICY_VERSION,
            )
        )
    for assessment_id, created_at, request in coordination_inputs:
        assessments.append(
            assess_coordination(
                request,
                policies,
                assessment_id=assessment_id,
                created_at=created_at,
                policy_version=SEED_POLICY_VERSION,
            )
        )
    return sorted(assessments, key=lambda item: item.created_at)


def build_seed_cases(
    assessments: list[AssessmentResponse],
) -> list[ReviewCase]:
    by_id = {assessment.assessment_id: assessment for assessment in assessments}
    definitions = [
        {
            "case_id": "C-2002",
            "assessment_id": "A-1002",
            "status": CaseStatus.OPEN,
            "priority": "high",
            "created_at": "2026-08-30T13:16:05Z",
        },
        {
            "case_id": "C-2003",
            "assessment_id": "A-1003",
            "status": CaseStatus.OPEN,
            "priority": "urgent",
            "created_at": "2026-08-30T13:19:05Z",
        },
        {
            "case_id": "C-2005",
            "assessment_id": "A-1005",
            "status": CaseStatus.IN_REVIEW,
            "priority": "urgent",
            "assigned_to": "Morgan Reed",
            "created_at": "2026-08-30T13:26:05Z",
            "review_started_at": "2026-08-30T13:50:00Z",
        },
        {
            "case_id": "C-2006",
            "assessment_id": "A-1006",
            "status": CaseStatus.RESOLVED,
            "priority": "high",
            "assigned_to": "Avery Chen",
            "outcome": ReviewOutcome.CONFIRMED_ABUSE,
            "resolution_notes": (
                "Direct threat confirmed; reversible account restrictions were applied."
            ),
            "created_at": "2026-08-30T13:30:05Z",
            "review_started_at": "2026-08-30T13:35:00Z",
            "resolved_at": "2026-08-30T13:41:00Z",
        },
        {
            "case_id": "C-2009",
            "assessment_id": "A-1009",
            "status": CaseStatus.RESOLVED,
            "priority": "high",
            "assigned_to": "Riley Park",
            "outcome": ReviewOutcome.FALSE_POSITIVE,
            "resolution_notes": (
                "Community workshop attendees shared a device and posted the same approved notice."
            ),
            "created_at": "2026-08-30T13:42:05Z",
            "review_started_at": "2026-08-30T13:47:00Z",
            "resolved_at": "2026-08-30T13:53:00Z",
        },
        {
            "case_id": "C-2010",
            "assessment_id": "A-1010",
            "status": CaseStatus.OPEN,
            "priority": "high",
            "created_at": "2026-08-30T13:46:05Z",
        },
    ]
    cases: list[ReviewCase] = []
    for definition in definitions:
        assessment = by_id[definition["assessment_id"]]
        cases.append(
            ReviewCase(
                case_id=definition["case_id"],
                assessment_id=assessment.assessment_id,
                subject_id=assessment.subject_id,
                assessment_type=assessment.assessment_type,
                risk_score=assessment.risk_score,
                risk_tier=assessment.risk_tier,
                priority=definition["priority"],
                status=definition["status"],
                summary=assessment.summary,
                evidence=assessment.signals,
                assigned_to=definition.get("assigned_to"),
                outcome=definition.get("outcome"),
                resolution_notes=definition.get("resolution_notes"),
                created_at=definition["created_at"],
                review_started_at=definition.get("review_started_at"),
                resolved_at=definition.get("resolved_at"),
            )
        )
    return cases
