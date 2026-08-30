"""Application service layer joining the pure engine to durable review state."""

from __future__ import annotations

import uuid
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
    RiskTier,
)
from marketplace_trust_starter.store import Store, utc_now


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


class TrustSafetyService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def _record(self, assessment: AssessmentResponse) -> AssessmentResponse:
        case: ReviewCase | None = None
        if assessment.requires_human_review:
            case_id = _new_id("C")
            assessment = assessment.model_copy(update={"case_id": case_id})
            priority = "urgent" if assessment.risk_tier is RiskTier.CRITICAL else "high"
            case = ReviewCase(
                case_id=case_id,
                assessment_id=assessment.assessment_id,
                subject_id=assessment.subject_id,
                assessment_type=assessment.assessment_type,
                risk_score=assessment.risk_score,
                risk_tier=assessment.risk_tier,
                priority=priority,
                status=CaseStatus.OPEN,
                summary=assessment.summary,
                evidence=assessment.signals,
                created_at=assessment.created_at,
            )
        self.store.record_assessment(assessment, case)
        return assessment

    def assess_profile(self, request: ProfileAssessmentRequest) -> AssessmentResponse:
        assessment = assess_profile(
            request,
            self.store.policy_map(),
            assessment_id=_new_id("A"),
            created_at=utc_now(),
            policy_version=self.store.policy_version(),
        )
        return self._record(assessment)

    def assess_content(self, request: ContentAssessmentRequest) -> AssessmentResponse:
        assessment = assess_content(
            request,
            self.store.policy_map(),
            assessment_id=_new_id("A"),
            created_at=utc_now(),
            policy_version=self.store.policy_version(),
        )
        return self._record(assessment)

    def assess_coordination(
        self,
        request: CoordinatedAbuseRequest,
    ) -> AssessmentResponse:
        assessment = assess_coordination(
            request,
            self.store.policy_map(),
            assessment_id=_new_id("A"),
            created_at=utc_now(),
            policy_version=self.store.policy_version(),
        )
        return self._record(assessment)

    @staticmethod
    def demo_scenarios() -> list[dict[str, Any]]:
        return [
            {
                "scenario_id": "ordinary-listing",
                "name": "Ordinary local listing",
                "description": "Shows a legitimate established seller remaining low risk.",
                "assessment_type": "content",
                "expected": "low",
            },
            {
                "scenario_id": "gift-card-scam",
                "name": "Gift-card solicitation",
                "description": (
                    "Combines a payment request, off-platform move, repetition, and reports."
                ),
                "assessment_type": "content",
                "expected": "high",
            },
            {
                "scenario_id": "coordinated-burst",
                "name": "Coordinated listing burst",
                "description": (
                    "Corroborates similarity, velocity, targeting, and shared infrastructure."
                ),
                "assessment_type": "coordinated_abuse",
                "expected": "critical",
            },
            {
                "scenario_id": "sparse-new-profile",
                "name": "Sparse new profile",
                "description": (
                    "Demonstrates that one weak signal stays below human-review threshold."
                ),
                "assessment_type": "profile",
                "expected": "low",
            },
        ]

    def run_demo_scenario(self, scenario_id: str) -> AssessmentResponse:
        if scenario_id == "ordinary-listing":
            return self.assess_content(
                ContentAssessmentRequest(
                    subject_id="demo-maple-merchant",
                    content_id="demo-listing-ordinary",
                    content_type="listing",
                    text="Oak side table in good condition. Local pickup near the library.",
                    account_age_days=520,
                    successful_transactions_90d=24,
                )
            )
        if scenario_id == "gift-card-scam":
            return self.assess_content(
                ContentAssessmentRequest(
                    subject_id="demo-amber-signal",
                    content_id="demo-message-scam",
                    content_type="message",
                    text=(
                        "Contact me on Telegram, buy a gift card, and send the code "
                        "to release your payment."
                    ),
                    account_age_days=1,
                    previous_similar_posts_1h=8,
                    unique_recipients_1h=17,
                    reports_24h=5,
                )
            )
        if scenario_id == "coordinated-burst":
            return self.assess_coordination(
                CoordinatedAbuseRequest(
                    cluster_id="demo-cluster-cascade",
                    participating_accounts=23,
                    new_account_ratio=0.87,
                    duplicate_content_ratio=0.93,
                    shared_device_ratio=0.76,
                    events_10m=214,
                    target_concentration=0.81,
                    independent_reports=11,
                    established_account_ratio=0.04,
                )
            )
        if scenario_id == "sparse-new-profile":
            return self.assess_profile(
                ProfileAssessmentRequest(
                    subject_id="demo-paper-crane",
                    bio="Just joined.",
                    account_age_days=1,
                    profile_completeness=0.2,
                    verified_contact=True,
                    media_count=1,
                    outbound_messages_1h=2,
                    unique_recipients_1h=2,
                )
            )
        raise KeyError(scenario_id)
