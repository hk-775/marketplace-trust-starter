"""Validated API contracts for assessments, policy controls, and human review."""

from __future__ import annotations

import re
from enum import StrEnum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

IDENTIFIER_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:-]{1,63}$"

# These fields are rejected before scoring. The product evaluates observable
# account/content behavior; it does not infer identity, demographics, health,
# appearance, or biometric characteristics.
PROHIBITED_INPUT_KEYS = {
    "age",
    "attractiveness",
    "attractivenessscore",
    "beauty",
    "biometric",
    "biometrics",
    "citizenship",
    "disability",
    "ethnicity",
    "face",
    "faceembedding",
    "facialfeatures",
    "facescore",
    "gender",
    "genderidentity",
    "health",
    "nationality",
    "personalappearance",
    "pregnancy",
    "protectedattribute",
    "race",
    "religion",
    "sex",
    "sexualorientation",
    "skintone",
}


def _normalized_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _find_prohibited_field(value: Any, path: str = "payload") -> str | None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = _normalized_key(str(key))
            if normalized in PROHIBITED_INPUT_KEYS:
                return f"{path}.{key}"
            found = _find_prohibited_field(child, f"{path}.{key}")
            if found:
                return found
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found = _find_prohibited_field(child, f"{path}[{index}]")
            if found:
                return found
    return None


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class GuardedInput(StrictModel):
    @model_validator(mode="before")
    @classmethod
    def reject_protected_or_appearance_fields(cls, value: Any) -> Any:
        found = _find_prohibited_field(value)
        if found:
            raise ValueError(
                f"{found} is prohibited: protected-attribute inference, biometrics, "
                "face analysis, and attractiveness/appearance scoring are out of scope"
            )
        return value


class AssessmentType(StrEnum):
    PROFILE = "profile"
    CONTENT = "content"
    COORDINATED_ABUSE = "coordinated_abuse"


class RiskTier(StrEnum):
    LOW = "low"
    GUARDED = "guarded"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"


class ReviewOutcome(StrEnum):
    CONFIRMED_ABUSE = "confirmed_abuse"
    FALSE_POSITIVE = "false_positive"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    NO_ACTION = "no_action"


class ContentType(StrEnum):
    MESSAGE = "message"
    LISTING = "listing"
    POST = "post"
    COMMENT = "comment"


class ProfileAssessmentRequest(GuardedInput):
    subject_id: str = Field(pattern=IDENTIFIER_PATTERN)
    bio: str = Field(default="", max_length=2_000)
    account_age_days: int = Field(ge=0, le=36_500)
    profile_completeness: float = Field(ge=0, le=1)
    verified_contact: bool = False
    media_count: int = Field(default=0, ge=0, le=50)
    outbound_messages_1h: int = Field(default=0, ge=0, le=10_000)
    unique_recipients_1h: int = Field(default=0, ge=0, le=10_000)
    bio_reuse_count_7d: int = Field(default=0, ge=0, le=10_000)
    linked_accounts_30d: int = Field(default=0, ge=0, le=10_000)
    prior_reports_30d: int = Field(default=0, ge=0, le=10_000)
    successful_transactions_90d: int = Field(default=0, ge=0, le=100_000)
    chargebacks_90d: int = Field(default=0, ge=0, le=100_000)


class ContentAssessmentRequest(GuardedInput):
    subject_id: str = Field(pattern=IDENTIFIER_PATTERN)
    content_id: str = Field(pattern=IDENTIFIER_PATTERN)
    content_type: ContentType
    text: str = Field(min_length=1, max_length=5_000)
    account_age_days: int = Field(default=0, ge=0, le=36_500)
    previous_similar_posts_1h: int = Field(default=0, ge=0, le=100_000)
    unique_recipients_1h: int = Field(default=1, ge=0, le=100_000)
    reports_24h: int = Field(default=0, ge=0, le=100_000)
    successful_transactions_90d: int = Field(default=0, ge=0, le=100_000)


class CoordinatedAbuseRequest(GuardedInput):
    cluster_id: str = Field(pattern=IDENTIFIER_PATTERN)
    participating_accounts: int = Field(ge=2, le=100_000)
    new_account_ratio: float = Field(ge=0, le=1)
    duplicate_content_ratio: float = Field(ge=0, le=1)
    shared_device_ratio: float = Field(ge=0, le=1)
    events_10m: int = Field(ge=0, le=1_000_000)
    target_concentration: float = Field(ge=0, le=1)
    independent_reports: int = Field(default=0, ge=0, le=100_000)
    established_account_ratio: float = Field(default=0, ge=0, le=1)


class SignalExplanation(StrictModel):
    signal_id: str
    category: str
    label: str
    description: str
    kind: Literal["risk", "counter_signal"]
    base_points: int
    multiplier: float
    points: int
    evidence: str


class AssessmentResponse(StrictModel):
    assessment_id: str
    assessment_type: AssessmentType
    subject_id: str
    created_at: str
    risk_score: int
    risk_tier: RiskTier
    confidence: float
    requires_human_review: bool
    recommended_action: str
    summary: str
    signals: list[SignalExplanation]
    counter_signals: list[SignalExplanation]
    policy_version: int
    case_id: str | None = None
    limitations: list[str]


class ReviewCase(StrictModel):
    case_id: str
    assessment_id: str
    subject_id: str
    assessment_type: AssessmentType
    risk_score: int
    risk_tier: RiskTier
    priority: Literal["standard", "high", "urgent"]
    status: CaseStatus
    summary: str
    evidence: list[SignalExplanation]
    assigned_to: str | None = None
    outcome: ReviewOutcome | None = None
    resolution_notes: str | None = None
    created_at: str
    review_started_at: str | None = None
    resolved_at: str | None = None
    human_decision_required: bool = True


class CaseUpdateRequest(StrictModel):
    status: CaseStatus
    reviewer: str = Field(min_length=2, max_length=80)
    outcome: ReviewOutcome | None = None
    resolution_notes: str | None = Field(default=None, max_length=2_000)

    @model_validator(mode="after")
    def validate_resolution(self) -> CaseUpdateRequest:
        if self.status is CaseStatus.RESOLVED:
            if self.outcome is None:
                raise ValueError("outcome is required when resolving a case")
            if not self.resolution_notes or len(self.resolution_notes) < 8:
                raise ValueError("resolution_notes must be at least 8 characters")
        elif self.outcome is not None or self.resolution_notes is not None:
            raise ValueError("outcome and resolution_notes are only valid for resolved cases")
        return self


class PolicyRule(StrictModel):
    policy_id: str
    name: str
    description: str
    category: str
    enabled: bool
    weight: float
    threshold: float
    default_enabled: bool
    default_weight: float
    default_threshold: float
    editable: bool
    version: int
    updated_at: str


class PolicyUpdateRequest(StrictModel):
    enabled: bool | None = None
    weight: float | None = Field(default=None, ge=0, le=2)
    threshold: float | None = Field(default=None, ge=0, le=100_000)
    actor: str = Field(min_length=2, max_length=80)
    reason: str = Field(min_length=5, max_length=500)

    @model_validator(mode="after")
    def require_change(self) -> PolicyUpdateRequest:
        if self.enabled is None and self.weight is None and self.threshold is None:
            raise ValueError("at least one of enabled, weight, or threshold is required")
        return self


class AuditEvent(StrictModel):
    audit_id: int
    timestamp: str
    actor: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]
    previous_hash: str
    event_hash: str


class PaginatedAssessments(StrictModel):
    items: list[AssessmentResponse]
    total: int


class PaginatedCases(StrictModel):
    items: list[ReviewCase]
    total: int


class AuditResponse(StrictModel):
    items: list[AuditEvent]
    total: int
    chain_valid: bool


class ResetRequest(StrictModel):
    actor: str = Field(default="demo-operator", min_length=2, max_length=80)
    confirmation: Literal["RESET DEMO"]


class ResetResponse(StrictModel):
    status: Literal["reset"]
    assessments: int
    cases: int
    policies: int
    audit_events: int
    reset_at: str
