"""Deterministic, explainable trust-and-safety scoring.

The engine intentionally uses observable behavior and content patterns only.
It does not load models, call external services, inspect images, infer protected
attributes, or produce an enforcement decision.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from marketplace_trust_starter.models import (
    AssessmentResponse,
    AssessmentType,
    ContentAssessmentRequest,
    CoordinatedAbuseRequest,
    ProfileAssessmentRequest,
    RiskTier,
    SignalExplanation,
)

PolicyMap = Mapping[str, Mapping[str, Any]]

LIMITATIONS = [
    "Rules identify documented patterns, not intent; context can change the correct outcome.",
    "Risk scores rank review priority and must not be treated as proof of abuse.",
    "No protected attributes, biometrics, faces, or appearance characteristics are evaluated.",
    (
        "Shared infrastructure and reports are supporting evidence only "
        "and can reflect benign behavior."
    ),
]

FINANCIAL_INSTRUMENTS = (
    "gift card",
    "wire transfer",
    "western union",
    "cash app",
    "cashapp",
    "venmo",
    "zelle",
    "crypto",
    "bitcoin",
    "usdt",
    "bank transfer",
)
FINANCIAL_ACTIONS = (
    "send",
    "buy",
    "purchase",
    "pay",
    "transfer",
    "deposit",
    "invest",
)
OFF_PLATFORM_SERVICES = ("telegram", "whatsapp", "signal app", "cashapp", "cash app")
OFF_PLATFORM_ACTIONS = ("message me", "contact me", "reach me", "add me", "dm me")

THREAT_PATTERNS = (
    re.compile(r"\bi(?:'m| am| will|'ll)?\s+(?:going to\s+)?(?:hurt|kill|attack)\s+you\b"),
    re.compile(r"\b(?:i\s+)?(?:will|'ll)\s+find\s+where\s+you\s+live\b"),
    re.compile(r"\b(?:i(?:'m| am)\s+)?coming\s+to\s+your\s+(?:home|house|work)\b"),
    re.compile(r"\byou(?:'ll| will)\s+(?:regret|pay for)\s+(?:this|that)\b"),
)


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text).lower()
    return re.sub(r"\s+", " ", normalized).strip()


def _rule(policies: PolicyMap, policy_id: str) -> Mapping[str, Any]:
    try:
        return policies[policy_id]
    except KeyError as exc:  # A missing rule is a configuration error, not a silent allow.
        raise ValueError(f"required policy rule is missing: {policy_id}") from exc


def _threshold(policies: PolicyMap, policy_id: str) -> float:
    return float(_rule(policies, policy_id)["threshold"])


def _signal(
    policies: PolicyMap,
    *,
    policy_id: str,
    category: str,
    label: str,
    description: str,
    base_points: int,
    evidence: str,
    kind: str = "risk",
) -> SignalExplanation | None:
    policy = _rule(policies, policy_id)
    if not bool(policy["enabled"]):
        return None
    multiplier = float(policy["weight"])
    points = round(base_points * multiplier)
    return SignalExplanation(
        signal_id=policy_id,
        category=category,
        label=label,
        description=description,
        kind=kind,  # type: ignore[arg-type]
        base_points=base_points,
        multiplier=multiplier,
        points=points,
        evidence=evidence,
    )


def _append(target: list[SignalExplanation], candidate: SignalExplanation | None) -> None:
    if candidate is not None:
        target.append(candidate)


def _contains_scam_solicitation(text: str) -> tuple[bool, list[str]]:
    normalized = _normalize(text)
    if not normalized:
        return False, []

    # Precision-first negation handling for common safety education language.
    safety_language = (
        "do not send",
        "don't send",
        "never send",
        "do not share",
        "don't share",
        "never share",
        "avoid paying",
        "scam awareness",
        "report a scam",
    )
    if any(phrase in normalized for phrase in safety_language):
        return False, []

    instruments = [item for item in FINANCIAL_INSTRUMENTS if item in normalized]
    actions = [
        item for item in FINANCIAL_ACTIONS if re.search(rf"\b{re.escape(item)}\b", normalized)
    ]
    guarantee = any(
        phrase in normalized
        for phrase in ("guaranteed return", "guaranteed profit", "double your money")
    )
    investment_context = any(
        phrase in normalized
        for phrase in ("investment", "crypto", "bitcoin", "trading opportunity")
    )
    matched = bool((instruments and actions) or (guarantee and investment_context))
    evidence = list(
        dict.fromkeys(instruments + actions + (["guaranteed return"] if guarantee else []))
    )
    return matched, evidence[:5]


def _contains_credential_harvesting(text: str) -> tuple[bool, list[str]]:
    normalized = _normalize(text)
    safety_language = (
        "never share your password",
        "do not share your password",
        "don't share your password",
        "never share a verification code",
        "do not share a verification code",
    )
    if any(phrase in normalized for phrase in safety_language):
        return False, []

    account_context = any(
        phrase in normalized
        for phrase in (
            "verify your account",
            "account suspended",
            "security check",
            "confirm your account",
        )
    )
    secret_request = any(
        phrase in normalized
        for phrase in (
            "password",
            "one-time code",
            "verification code",
            "security code",
            "login code",
        )
    )
    link_context = bool(
        re.search(r"https?://|www\.|click (?:this|the) link|log ?in here", normalized)
    )
    matched = (account_context and link_context) or (account_context and secret_request)
    evidence = []
    if account_context:
        evidence.append("account-verification language")
    if secret_request:
        evidence.append("secret/code request")
    if link_context:
        evidence.append("login or link prompt")
    return matched, evidence


def _contains_targeted_threat(text: str) -> tuple[bool, str]:
    normalized = _normalize(text)
    for pattern in THREAT_PATTERNS:
        match = pattern.search(normalized)
        if match:
            return True, match.group(0)
    return False, ""


def _off_platform_solicitation(text: str) -> tuple[bool, list[str]]:
    normalized = _normalize(text)
    services = [service for service in OFF_PLATFORM_SERVICES if service in normalized]
    actions = [action for action in OFF_PLATFORM_ACTIONS if action in normalized]
    return bool(services and actions), list(dict.fromkeys(services + actions))[:4]


def _finalize(
    *,
    assessment_id: str,
    assessment_type: AssessmentType,
    subject_id: str,
    created_at: str,
    policies: PolicyMap,
    policy_version: int,
    risk_signals: list[SignalExplanation],
    counter_signals: list[SignalExplanation],
) -> AssessmentResponse:
    raw_score = sum(signal.points for signal in risk_signals + counter_signals)
    risk_score = max(0, min(100, raw_score))

    guarded_threshold = int(_threshold(policies, "risk_guarded_threshold"))
    review_threshold = int(_threshold(policies, "human_review_gate"))
    critical_threshold = int(_threshold(policies, "risk_critical_threshold"))

    if risk_score >= critical_threshold:
        risk_tier = RiskTier.CRITICAL
    elif risk_score >= review_threshold:
        risk_tier = RiskTier.HIGH
    elif risk_score >= guarded_threshold:
        risk_tier = RiskTier.GUARDED
    else:
        risk_tier = RiskTier.LOW

    requires_review = risk_score >= review_threshold
    if risk_tier is RiskTier.CRITICAL:
        recommended_action = "prioritize_human_review_and_apply_reversible_friction"
    elif risk_tier is RiskTier.HIGH:
        recommended_action = "queue_for_human_review"
    elif risk_tier is RiskTier.GUARDED:
        recommended_action = "monitor_and_collect_more_context"
    else:
        recommended_action = "allow_with_standard_controls"

    categories = {signal.category for signal in risk_signals}
    if risk_signals:
        confidence = min(0.98, 0.62 + (0.08 * len(categories)) + (0.025 * len(risk_signals)))
    else:
        # This means confidence that no documented rule fired, not certainty that
        # the actor/content is safe.
        confidence = 0.84 if counter_signals else 0.78

    risk_count = len(risk_signals)
    counter_count = len(counter_signals)
    summary = (
        f"{risk_count} risk signal{'s' if risk_count != 1 else ''} and "
        f"{counter_count} counter-signal{'s' if counter_count != 1 else ''} "
        f"produced a {risk_tier.value} review priority."
    )

    return AssessmentResponse(
        assessment_id=assessment_id,
        assessment_type=assessment_type,
        subject_id=subject_id,
        created_at=created_at,
        risk_score=risk_score,
        risk_tier=risk_tier,
        confidence=round(confidence, 2),
        requires_human_review=requires_review,
        recommended_action=recommended_action,
        summary=summary,
        signals=risk_signals,
        counter_signals=counter_signals,
        policy_version=policy_version,
        limitations=LIMITATIONS,
    )


def assess_profile(
    request: ProfileAssessmentRequest,
    policies: PolicyMap,
    *,
    assessment_id: str,
    created_at: str,
    policy_version: int,
) -> AssessmentResponse:
    risk_signals: list[SignalExplanation] = []
    counter_signals: list[SignalExplanation] = []

    if (
        request.profile_completeness < _threshold(policies, "profile_completeness")
        and request.account_age_days <= 7
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_completeness",
                category="profile",
                label="Sparse new profile",
                description="Low completeness is considered only when the account is new.",
                base_points=12,
                evidence=(
                    f"completeness={request.profile_completeness:.0%}; "
                    f"account_age_days={request.account_age_days}"
                ),
            ),
        )

    if (
        request.account_age_days <= 7
        and request.outbound_messages_1h >= _threshold(policies, "profile_velocity")
        and request.unique_recipients_1h >= 6
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_velocity",
                category="behavior",
                label="New-account outreach burst",
                description="A new account contacted many distinct recipients in one hour.",
                base_points=18,
                evidence=(
                    f"messages_1h={request.outbound_messages_1h}; "
                    f"unique_recipients_1h={request.unique_recipients_1h}"
                ),
            ),
        )

    if request.bio_reuse_count_7d >= _threshold(policies, "profile_reuse"):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_reuse",
                category="coordination",
                label="Repeated profile text",
                description="The same profile text appeared across multiple recent accounts.",
                base_points=20,
                evidence=f"bio_reuse_count_7d={request.bio_reuse_count_7d}",
            ),
        )

    scam_match, scam_evidence = _contains_scam_solicitation(request.bio)
    if scam_match:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_scam_language",
                category="content",
                label="Financial solicitation in profile",
                description="Profile text combines a payment instrument with a solicitation.",
                base_points=30,
                evidence=", ".join(scam_evidence),
            ),
        )

    if request.prior_reports_30d >= _threshold(policies, "profile_report_history"):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_report_history",
                category="reports",
                label="Independent report volume",
                description="Recent reports add context but are capped as supporting evidence.",
                base_points=14,
                evidence=f"prior_reports_30d={request.prior_reports_30d}",
            ),
        )

    if request.chargebacks_90d >= _threshold(policies, "profile_payment_abuse"):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_payment_abuse",
                category="transactions",
                label="Recent payment reversals",
                description="Multiple recent chargebacks can indicate transaction abuse.",
                base_points=22,
                evidence=(
                    f"chargebacks_90d={request.chargebacks_90d}; "
                    f"successful_transactions_90d={request.successful_transactions_90d}"
                ),
            ),
        )

    if (
        request.linked_accounts_30d >= _threshold(policies, "profile_linkage")
        and request.bio_reuse_count_7d > 0
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="profile_linkage",
                category="coordination",
                label="Linked-account reuse",
                description="Account linkage is counted only with corroborating content reuse.",
                base_points=16,
                evidence=(
                    f"linked_accounts_30d={request.linked_accounts_30d}; "
                    f"bio_reuse_count_7d={request.bio_reuse_count_7d}"
                ),
            ),
        )

    if request.verified_contact:
        _append(
            counter_signals,
            _signal(
                policies,
                policy_id="verified_contact_counter",
                category="account_history",
                label="Verified contact channel",
                description="A verified contact channel modestly reduces uncertainty.",
                base_points=-5,
                evidence="verified_contact=true",
                kind="counter_signal",
            ),
        )

    if (
        request.account_age_days >= _threshold(policies, "established_history_counter")
        and request.successful_transactions_90d >= 5
        and request.prior_reports_30d == 0
        and request.chargebacks_90d == 0
    ):
        _append(
            counter_signals,
            _signal(
                policies,
                policy_id="established_history_counter",
                category="account_history",
                label="Established positive history",
                description="Sustained successful activity with no recent reports reduces risk.",
                base_points=-12,
                evidence=(
                    f"account_age_days={request.account_age_days}; "
                    f"successful_transactions_90d={request.successful_transactions_90d}"
                ),
                kind="counter_signal",
            ),
        )

    if request.profile_completeness >= 0.8:
        _append(
            counter_signals,
            _signal(
                policies,
                policy_id="complete_profile_counter",
                category="profile",
                label="Substantive profile",
                description="A substantially complete profile modestly reduces uncertainty.",
                base_points=-4,
                evidence=f"profile_completeness={request.profile_completeness:.0%}",
                kind="counter_signal",
            ),
        )

    return _finalize(
        assessment_id=assessment_id,
        assessment_type=AssessmentType.PROFILE,
        subject_id=request.subject_id,
        created_at=created_at,
        policies=policies,
        policy_version=policy_version,
        risk_signals=risk_signals,
        counter_signals=counter_signals,
    )


def assess_content(
    request: ContentAssessmentRequest,
    policies: PolicyMap,
    *,
    assessment_id: str,
    created_at: str,
    policy_version: int,
) -> AssessmentResponse:
    risk_signals: list[SignalExplanation] = []
    counter_signals: list[SignalExplanation] = []

    scam_match, scam_evidence = _contains_scam_solicitation(request.text)
    if scam_match:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_scam",
                category="scam",
                label="Payment or investment solicitation",
                description="The content combines a financial instrument with a requested action.",
                base_points=34,
                evidence=", ".join(scam_evidence),
            ),
        )

    credential_match, credential_evidence = _contains_credential_harvesting(request.text)
    if credential_match:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_credentials",
                category="malicious_content",
                label="Credential-harvesting pattern",
                description=(
                    "Account-verification language is paired with a secret or login prompt."
                ),
                base_points=36,
                evidence=", ".join(credential_evidence),
            ),
        )

    threat_match, threat_evidence = _contains_targeted_threat(request.text)
    if threat_match:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_threat",
                category="malicious_content",
                label="Direct targeted threat",
                description="A high-precision direct threat pattern was found.",
                base_points=42,
                evidence=threat_evidence,
            ),
        )

    if (
        request.previous_similar_posts_1h >= _threshold(policies, "content_spam_repetition")
        and request.unique_recipients_1h >= 5
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_spam_repetition",
                category="spam",
                label="Repeated content distribution",
                description="Near-identical content reached multiple recipients in a short period.",
                base_points=22,
                evidence=(
                    f"similar_posts_1h={request.previous_similar_posts_1h}; "
                    f"unique_recipients_1h={request.unique_recipients_1h}"
                ),
            ),
        )

    if (
        request.unique_recipients_1h >= _threshold(policies, "content_spam_burst")
        and request.account_age_days <= 14
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_spam_burst",
                category="spam",
                label="New-account distribution burst",
                description="A new account distributed content to unusually many recipients.",
                base_points=18,
                evidence=(
                    f"account_age_days={request.account_age_days}; "
                    f"unique_recipients_1h={request.unique_recipients_1h}"
                ),
            ),
        )

    off_platform, off_platform_evidence = _off_platform_solicitation(request.text)
    if off_platform and (request.account_age_days <= 14 or scam_match):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_off_platform",
                category="scam",
                label="Risk-context off-platform move",
                description=(
                    "Off-platform solicitation is counted only with new-account or scam context."
                ),
                base_points=10,
                evidence=", ".join(off_platform_evidence),
            ),
        )

    if request.reports_24h >= _threshold(policies, "content_report_history"):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="content_report_history",
                category="reports",
                label="Independent report volume",
                description="Recent reports add supporting context but do not prove a violation.",
                base_points=12,
                evidence=f"reports_24h={request.reports_24h}",
            ),
        )

    if (
        request.account_age_days >= 365
        and request.successful_transactions_90d >= 10
        and request.reports_24h == 0
    ):
        _append(
            counter_signals,
            _signal(
                policies,
                policy_id="content_history_counter",
                category="account_history",
                label="Established positive activity",
                description="Longstanding successful activity modestly reduces uncertainty.",
                base_points=-8,
                evidence=(
                    f"account_age_days={request.account_age_days}; "
                    f"successful_transactions_90d={request.successful_transactions_90d}"
                ),
                kind="counter_signal",
            ),
        )

    return _finalize(
        assessment_id=assessment_id,
        assessment_type=AssessmentType.CONTENT,
        subject_id=request.subject_id,
        created_at=created_at,
        policies=policies,
        policy_version=policy_version,
        risk_signals=risk_signals,
        counter_signals=counter_signals,
    )


def assess_coordination(
    request: CoordinatedAbuseRequest,
    policies: PolicyMap,
    *,
    assessment_id: str,
    created_at: str,
    policy_version: int,
) -> AssessmentResponse:
    risk_signals: list[SignalExplanation] = []
    counter_signals: list[SignalExplanation] = []

    similarity_triggered = (
        request.duplicate_content_ratio >= _threshold(policies, "coordination_similarity")
        and request.participating_accounts >= 4
    )
    velocity_triggered = (
        request.events_10m >= _threshold(policies, "coordination_velocity")
        and request.participating_accounts >= 5
    )

    if similarity_triggered:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="coordination_similarity",
                category="coordination",
                label="Cross-account content similarity",
                description="Multiple accounts posted substantially duplicated content.",
                base_points=28,
                evidence=(
                    f"accounts={request.participating_accounts}; "
                    f"duplicate_content_ratio={request.duplicate_content_ratio:.0%}"
                ),
            ),
        )

    if velocity_triggered:
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="coordination_velocity",
                category="coordination",
                label="Synchronized activity burst",
                description="The cluster produced a concentrated burst of events.",
                base_points=20,
                evidence=f"events_10m={request.events_10m}",
            ),
        )

    if (
        request.target_concentration >= _threshold(policies, "coordination_targeting")
        and request.independent_reports >= 3
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="coordination_targeting",
                category="targeting",
                label="Concentrated target pressure",
                description="Activity concentrated on a small target set with independent reports.",
                base_points=22,
                evidence=(
                    f"target_concentration={request.target_concentration:.0%}; "
                    f"independent_reports={request.independent_reports}"
                ),
            ),
        )

    if request.shared_device_ratio >= _threshold(
        policies, "coordination_shared_infrastructure"
    ) and (similarity_triggered or velocity_triggered):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="coordination_shared_infrastructure",
                category="coordination",
                label="Corroborating shared infrastructure",
                description=(
                    "Shared device context is counted only with independent coordination evidence."
                ),
                base_points=12,
                evidence=f"shared_device_ratio={request.shared_device_ratio:.0%}",
            ),
        )

    if (
        request.new_account_ratio >= _threshold(policies, "coordination_new_accounts")
        and request.duplicate_content_ratio >= 0.5
    ):
        _append(
            risk_signals,
            _signal(
                policies,
                policy_id="coordination_new_accounts",
                category="coordination",
                label="New-account cluster",
                description=(
                    "A mostly new-account cluster also shared substantially duplicated content."
                ),
                base_points=18,
                evidence=(
                    f"new_account_ratio={request.new_account_ratio:.0%}; "
                    f"duplicate_content_ratio={request.duplicate_content_ratio:.0%}"
                ),
            ),
        )

    if (
        request.established_account_ratio >= 0.7
        and request.duplicate_content_ratio < 0.5
        and request.independent_reports == 0
    ):
        _append(
            counter_signals,
            _signal(
                policies,
                policy_id="coordination_history_counter",
                category="account_history",
                label="Established, diverse cluster",
                description=(
                    "Mostly established accounts with diverse content reduce coordination concern."
                ),
                base_points=-10,
                evidence=(
                    f"established_account_ratio={request.established_account_ratio:.0%}; "
                    f"duplicate_content_ratio={request.duplicate_content_ratio:.0%}"
                ),
                kind="counter_signal",
            ),
        )

    return _finalize(
        assessment_id=assessment_id,
        assessment_type=AssessmentType.COORDINATED_ABUSE,
        subject_id=request.cluster_id,
        created_at=created_at,
        policies=policies,
        policy_version=policy_version,
        risk_signals=risk_signals,
        counter_signals=counter_signals,
    )
