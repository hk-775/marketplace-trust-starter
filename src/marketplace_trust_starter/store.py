"""SQLite persistence for demo state, review workflow, policy controls, and audit."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from marketplace_trust_starter.models import (
    AssessmentResponse,
    AuditEvent,
    CaseStatus,
    CaseUpdateRequest,
    PolicyRule,
    PolicyUpdateRequest,
    ReviewCase,
)
from marketplace_trust_starter.seed import (
    SEED_POLICY_VERSION,
    build_seed_assessments,
    build_seed_cases,
    default_policy_rows,
)

ZERO_HASH = "0" * 64


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


class Store:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS policies (
                    policy_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    enabled INTEGER NOT NULL,
                    weight REAL NOT NULL,
                    threshold REAL NOT NULL,
                    default_enabled INTEGER NOT NULL,
                    default_weight REAL NOT NULL,
                    default_threshold REAL NOT NULL,
                    editable INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS assessments (
                    assessment_id TEXT PRIMARY KEY,
                    assessment_type TEXT NOT NULL,
                    subject_id TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_tier TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_assessments_created
                    ON assessments(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_assessments_tier
                    ON assessments(risk_tier);

                CREATE TABLE IF NOT EXISTS cases (
                    case_id TEXT PRIMARY KEY,
                    assessment_id TEXT NOT NULL UNIQUE,
                    subject_id TEXT NOT NULL,
                    assessment_type TEXT NOT NULL,
                    risk_score INTEGER NOT NULL,
                    risk_tier TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    status TEXT NOT NULL,
                    assigned_to TEXT,
                    outcome TEXT,
                    created_at TEXT NOT NULL,
                    review_started_at TEXT,
                    resolved_at TEXT,
                    payload_json TEXT NOT NULL,
                    FOREIGN KEY (assessment_id) REFERENCES assessments(assessment_id)
                );
                CREATE INDEX IF NOT EXISTS idx_cases_status
                    ON cases(status, priority, created_at);

                CREATE TABLE IF NOT EXISTS audit_events (
                    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    event_hash TEXT NOT NULL UNIQUE
                );
                CREATE INDEX IF NOT EXISTS idx_audit_timestamp
                    ON audit_events(timestamp DESC);
                """
            )
            connection.commit()
            count = connection.execute("SELECT COUNT(*) FROM policies").fetchone()[0]
        if count == 0:
            self.reset_demo(actor="system-seed")

    def _insert_policy(self, connection: sqlite3.Connection, row: dict[str, Any]) -> None:
        connection.execute(
            """
            INSERT INTO policies (
                policy_id, name, description, category, enabled, weight, threshold,
                default_enabled, default_weight, default_threshold, editable,
                version, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["policy_id"],
                row["name"],
                row["description"],
                row["category"],
                int(row["enabled"]),
                row["weight"],
                row["threshold"],
                int(row["default_enabled"]),
                row["default_weight"],
                row["default_threshold"],
                int(row["editable"]),
                row["version"],
                row["updated_at"],
            ),
        )

    def _insert_assessment(
        self,
        connection: sqlite3.Connection,
        assessment: AssessmentResponse,
    ) -> None:
        connection.execute(
            """
            INSERT INTO assessments (
                assessment_id, assessment_type, subject_id, created_at,
                risk_score, risk_tier, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                assessment.assessment_id,
                assessment.assessment_type.value,
                assessment.subject_id,
                assessment.created_at,
                assessment.risk_score,
                assessment.risk_tier.value,
                assessment.model_dump_json(),
            ),
        )

    def _insert_case(self, connection: sqlite3.Connection, case: ReviewCase) -> None:
        connection.execute(
            """
            INSERT INTO cases (
                case_id, assessment_id, subject_id, assessment_type, risk_score,
                risk_tier, priority, status, assigned_to, outcome, created_at,
                review_started_at, resolved_at, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                case.case_id,
                case.assessment_id,
                case.subject_id,
                case.assessment_type.value,
                case.risk_score,
                case.risk_tier.value,
                case.priority,
                case.status.value,
                case.assigned_to,
                case.outcome.value if case.outcome else None,
                case.created_at,
                case.review_started_at,
                case.resolved_at,
                case.model_dump_json(),
            ),
        )

    def _append_audit(
        self,
        connection: sqlite3.Connection,
        *,
        timestamp: str,
        actor: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict[str, Any],
    ) -> None:
        previous_row = connection.execute(
            "SELECT event_hash FROM audit_events ORDER BY audit_id DESC LIMIT 1"
        ).fetchone()
        previous_hash = previous_row["event_hash"] if previous_row else ZERO_HASH
        details_json = json.dumps(details, sort_keys=True, separators=(",", ":"))
        canonical = json.dumps(
            {
                "timestamp": timestamp,
                "actor": actor,
                "action": action,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "details": json.loads(details_json),
                "previous_hash": previous_hash,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        event_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        connection.execute(
            """
            INSERT INTO audit_events (
                timestamp, actor, action, entity_type, entity_id,
                details_json, previous_hash, event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                actor,
                action,
                entity_type,
                entity_id,
                details_json,
                previous_hash,
                event_hash,
            ),
        )

    def reset_demo(self, *, actor: str) -> dict[str, Any]:
        policy_rows = default_policy_rows()
        assessments = build_seed_assessments(policy_rows)
        cases = build_seed_cases(assessments)
        case_by_assessment = {case.assessment_id: case.case_id for case in cases}
        assessments = [
            assessment.model_copy(
                update={"case_id": case_by_assessment.get(assessment.assessment_id)}
            )
            for assessment in assessments
        ]
        reset_at = utc_now()

        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("DELETE FROM audit_events")
            connection.execute("DELETE FROM cases")
            connection.execute("DELETE FROM assessments")
            connection.execute("DELETE FROM policies")
            connection.execute("DELETE FROM settings")
            connection.execute(
                "INSERT INTO settings (key, value) VALUES ('policy_version', ?)",
                (str(SEED_POLICY_VERSION),),
            )
            for row in policy_rows:
                self._insert_policy(connection, row)
            for assessment in assessments:
                self._insert_assessment(connection, assessment)
            for case in cases:
                self._insert_case(connection, case)

            self._append_audit(
                connection,
                timestamp="2026-08-30T13:00:00Z",
                actor="system-seed",
                action="ethical_boundary_loaded",
                entity_type="policy",
                entity_id="protected_attribute_guard",
                details={
                    "protected_attribute_inference": "prohibited",
                    "face_and_attractiveness_scoring": "prohibited",
                },
            )
            for assessment in assessments:
                self._append_audit(
                    connection,
                    timestamp=assessment.created_at,
                    actor="demo-signal-engine",
                    action="assessment_recorded",
                    entity_type="assessment",
                    entity_id=assessment.assessment_id,
                    details={
                        "risk_score": assessment.risk_score,
                        "risk_tier": assessment.risk_tier.value,
                        "requires_human_review": assessment.requires_human_review,
                    },
                )
            for case in cases:
                self._append_audit(
                    connection,
                    timestamp=case.created_at,
                    actor="demo-review-router",
                    action="case_created",
                    entity_type="case",
                    entity_id=case.case_id,
                    details={
                        "assessment_id": case.assessment_id,
                        "priority": case.priority,
                        "human_decision_required": True,
                    },
                )
                if case.review_started_at:
                    self._append_audit(
                        connection,
                        timestamp=case.review_started_at,
                        actor=case.assigned_to or "demo-reviewer",
                        action="review_started",
                        entity_type="case",
                        entity_id=case.case_id,
                        details={"reviewer": case.assigned_to},
                    )
                if case.resolved_at:
                    self._append_audit(
                        connection,
                        timestamp=case.resolved_at,
                        actor=case.assigned_to or "demo-reviewer",
                        action="case_resolved",
                        entity_type="case",
                        entity_id=case.case_id,
                        details={
                            "outcome": case.outcome.value if case.outcome else None,
                            "resolution_notes": case.resolution_notes,
                        },
                    )
            self._append_audit(
                connection,
                timestamp=reset_at,
                actor=actor,
                action="demo_reset",
                entity_type="demo",
                entity_id="seed-v1",
                details={
                    "assessments": len(assessments),
                    "cases": len(cases),
                    "policies": len(policy_rows),
                },
            )
            connection.commit()
            audit_count = connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0]

        return {
            "status": "reset",
            "assessments": len(assessments),
            "cases": len(cases),
            "policies": len(policy_rows),
            "audit_events": audit_count,
            "reset_at": reset_at,
        }

    def policy_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = 'policy_version'"
            ).fetchone()
        return int(row["value"]) if row else 1

    def policy_map(self) -> dict[str, dict[str, Any]]:
        return {policy.policy_id: policy.model_dump() for policy in self.list_policies()}

    def list_policies(self) -> list[PolicyRule]:
        with self.connect() as connection:
            rows = connection.execute("SELECT * FROM policies ORDER BY category, name").fetchall()
        return [
            PolicyRule(
                policy_id=row["policy_id"],
                name=row["name"],
                description=row["description"],
                category=row["category"],
                enabled=bool(row["enabled"]),
                weight=row["weight"],
                threshold=row["threshold"],
                default_enabled=bool(row["default_enabled"]),
                default_weight=row["default_weight"],
                default_threshold=row["default_threshold"],
                editable=bool(row["editable"]),
                version=row["version"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def update_policy(self, policy_id: str, update: PolicyUpdateRequest) -> PolicyRule:
        changed_at = utc_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT * FROM policies WHERE policy_id = ?", (policy_id,)
            ).fetchone()
            if row is None:
                raise KeyError(policy_id)
            if not bool(row["editable"]):
                raise PermissionError(f"policy {policy_id} is a locked safety boundary")

            before = {
                "enabled": bool(row["enabled"]),
                "weight": row["weight"],
                "threshold": row["threshold"],
            }
            after = {
                "enabled": update.enabled if update.enabled is not None else before["enabled"],
                "weight": update.weight if update.weight is not None else before["weight"],
                "threshold": (
                    update.threshold if update.threshold is not None else before["threshold"]
                ),
            }
            version = int(row["version"]) + 1
            connection.execute(
                """
                UPDATE policies
                SET enabled = ?, weight = ?, threshold = ?, version = ?, updated_at = ?
                WHERE policy_id = ?
                """,
                (
                    int(after["enabled"]),
                    after["weight"],
                    after["threshold"],
                    version,
                    changed_at,
                    policy_id,
                ),
            )
            current_policy_version = int(
                connection.execute(
                    "SELECT value FROM settings WHERE key = 'policy_version'"
                ).fetchone()["value"]
            )
            connection.execute(
                "UPDATE settings SET value = ? WHERE key = 'policy_version'",
                (str(current_policy_version + 1),),
            )
            self._append_audit(
                connection,
                timestamp=changed_at,
                actor=update.actor,
                action="policy_updated",
                entity_type="policy",
                entity_id=policy_id,
                details={"before": before, "after": after, "reason": update.reason},
            )
            connection.commit()
        return next(policy for policy in self.list_policies() if policy.policy_id == policy_id)

    def record_assessment(
        self,
        assessment: AssessmentResponse,
        case: ReviewCase | None,
        *,
        actor: str = "signal-engine",
    ) -> None:
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._insert_assessment(connection, assessment)
            self._append_audit(
                connection,
                timestamp=assessment.created_at,
                actor=actor,
                action="assessment_recorded",
                entity_type="assessment",
                entity_id=assessment.assessment_id,
                details={
                    "risk_score": assessment.risk_score,
                    "risk_tier": assessment.risk_tier.value,
                    "signal_ids": [signal.signal_id for signal in assessment.signals],
                    "requires_human_review": assessment.requires_human_review,
                },
            )
            if case is not None:
                self._insert_case(connection, case)
                self._append_audit(
                    connection,
                    timestamp=case.created_at,
                    actor="review-router",
                    action="case_created",
                    entity_type="case",
                    entity_id=case.case_id,
                    details={
                        "assessment_id": case.assessment_id,
                        "priority": case.priority,
                        "human_decision_required": True,
                    },
                )
            connection.commit()

    def list_assessments(self, *, limit: int = 50) -> tuple[list[AssessmentResponse], int]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT payload_json FROM assessments ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            total = connection.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
        return [AssessmentResponse.model_validate_json(row["payload_json"]) for row in rows], total

    def list_cases(
        self,
        *,
        status: CaseStatus | None = None,
        limit: int = 100,
    ) -> tuple[list[ReviewCase], int]:
        where = ""
        parameters: list[Any] = []
        if status is not None:
            where = "WHERE status = ?"
            parameters.append(status.value)
        parameters.append(limit)
        priority_order = "CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 ELSE 2 END"
        with self.connect() as connection:
            rows = connection.execute(
                f"""
                SELECT payload_json FROM cases {where}
                ORDER BY {priority_order}, created_at DESC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
            count_query = f"SELECT COUNT(*) FROM cases {where}"
            total = connection.execute(count_query, parameters[:-1]).fetchone()[0]
        return [ReviewCase.model_validate_json(row["payload_json"]) for row in rows], total

    def get_case(self, case_id: str) -> ReviewCase:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT payload_json FROM cases WHERE case_id = ?", (case_id,)
            ).fetchone()
        if row is None:
            raise KeyError(case_id)
        return ReviewCase.model_validate_json(row["payload_json"])

    def update_case(self, case_id: str, update: CaseUpdateRequest) -> ReviewCase:
        changed_at = utc_now()
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT payload_json FROM cases WHERE case_id = ?", (case_id,)
            ).fetchone()
            if row is None:
                raise KeyError(case_id)
            current = ReviewCase.model_validate_json(row["payload_json"])

            if current.status is CaseStatus.RESOLVED:
                raise ValueError("resolved cases are immutable")
            if current.status is CaseStatus.OPEN and update.status is CaseStatus.RESOLVED:
                raise ValueError("a case must enter in_review before it can be resolved")
            if current.status is CaseStatus.IN_REVIEW and update.status is CaseStatus.OPEN:
                raise ValueError("an in-review case cannot return to open")
            if update.status is CaseStatus.OPEN:
                raise ValueError("use in_review to claim an open case")

            if update.status is CaseStatus.IN_REVIEW:
                updated = current.model_copy(
                    update={
                        "status": CaseStatus.IN_REVIEW,
                        "assigned_to": update.reviewer,
                        "review_started_at": current.review_started_at or changed_at,
                    }
                )
                action = (
                    "review_started" if current.status is CaseStatus.OPEN else "review_reassigned"
                )
                details = {"reviewer": update.reviewer}
            else:
                if current.status is not CaseStatus.IN_REVIEW:
                    raise ValueError("only an in-review case can be resolved")
                updated = current.model_copy(
                    update={
                        "status": CaseStatus.RESOLVED,
                        "assigned_to": update.reviewer,
                        "outcome": update.outcome,
                        "resolution_notes": update.resolution_notes,
                        "resolved_at": changed_at,
                    }
                )
                action = "case_resolved"
                details = {
                    "reviewer": update.reviewer,
                    "outcome": update.outcome.value if update.outcome else None,
                    "resolution_notes": update.resolution_notes,
                }

            connection.execute(
                """
                UPDATE cases
                SET status = ?, assigned_to = ?, outcome = ?, review_started_at = ?,
                    resolved_at = ?, payload_json = ?
                WHERE case_id = ?
                """,
                (
                    updated.status.value,
                    updated.assigned_to,
                    updated.outcome.value if updated.outcome else None,
                    updated.review_started_at,
                    updated.resolved_at,
                    updated.model_dump_json(),
                    case_id,
                ),
            )
            self._append_audit(
                connection,
                timestamp=changed_at,
                actor=update.reviewer,
                action=action,
                entity_type="case",
                entity_id=case_id,
                details=details,
            )
            connection.commit()
        return updated

    def metrics(self) -> dict[str, Any]:
        assessments, assessment_total = self.list_assessments(limit=10_000)
        cases, case_total = self.list_cases(limit=10_000)
        tier_counts = Counter(item.risk_tier.value for item in assessments)
        status_counts = Counter(item.status.value for item in cases)
        outcome_counts = Counter(item.outcome.value for item in cases if item.outcome)
        scores = sorted(item.risk_score for item in assessments)
        median_score = scores[len(scores) // 2] if scores else 0
        review_queue = sum(
            1 for case in cases if case.status in {CaseStatus.OPEN, CaseStatus.IN_REVIEW}
        )
        high_or_critical = sum(
            1 for item in assessments if item.risk_tier.value in {"high", "critical"}
        )
        false_positive_count = outcome_counts.get("false_positive", 0)
        resolved_count = status_counts.get("resolved", 0)
        return {
            "generated_at": utc_now(),
            "kpis": {
                "total_assessments": assessment_total,
                "review_queue": review_queue,
                "high_or_critical_rate": (
                    round(high_or_critical / assessment_total, 3) if assessment_total else 0
                ),
                "median_risk_score": median_score,
                "false_positive_review_rate": (
                    round(false_positive_count / resolved_count, 3) if resolved_count else 0
                ),
            },
            "tier_distribution": {
                tier: tier_counts.get(tier, 0) for tier in ("low", "guarded", "high", "critical")
            },
            "case_status_distribution": {
                status: status_counts.get(status, 0) for status in ("open", "in_review", "resolved")
            },
            "review_outcomes": dict(outcome_counts),
            "total_cases": case_total,
            "policy_version": self.policy_version(),
        }

    def insights(self) -> dict[str, Any]:
        assessments, _ = self.list_assessments(limit=10_000)
        hits: Counter[str] = Counter()
        contributions: Counter[str] = Counter()
        counters: Counter[str] = Counter()
        for assessment in assessments:
            for signal in assessment.signals:
                hits[signal.signal_id] += 1
                contributions[signal.signal_id] += signal.points
            for signal in assessment.counter_signals:
                counters[signal.signal_id] += 1
        policies = {policy.policy_id: policy for policy in self.list_policies()}
        top_signals = []
        for signal_id, hit_count in hits.most_common():
            policy = policies[signal_id]
            top_signals.append(
                {
                    "signal_id": signal_id,
                    "name": policy.name,
                    "category": policy.category,
                    "hits": hit_count,
                    "average_points": round(contributions[signal_id] / hit_count, 1),
                    "enabled": policy.enabled,
                }
            )
        return {
            "engine": {
                "type": "deterministic_rules",
                "external_models": 0,
                "network_calls": 0,
                "policy_version": self.policy_version(),
            },
            "top_signals": top_signals,
            "counter_signal_hits": [
                {
                    "signal_id": signal_id,
                    "name": policies[signal_id].name,
                    "hits": count,
                }
                for signal_id, count in counters.most_common()
            ],
            "safeguards": [
                "Protected-attribute inference is rejected at validation.",
                "Face, biometric, attractiveness, and appearance scoring are prohibited.",
                "High scores create human review cases; they do not execute punishment.",
                "Reports and shared infrastructure are supporting evidence only.",
            ],
        }

    def audit_events(self, *, limit: int = 100) -> tuple[list[AuditEvent], int, bool]:
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM audit_events ORDER BY audit_id DESC LIMIT ?", (limit,)
            ).fetchall()
            all_rows = connection.execute(
                "SELECT * FROM audit_events ORDER BY audit_id ASC"
            ).fetchall()
        events = [
            AuditEvent(
                audit_id=row["audit_id"],
                timestamp=row["timestamp"],
                actor=row["actor"],
                action=row["action"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                details=json.loads(row["details_json"]),
                previous_hash=row["previous_hash"],
                event_hash=row["event_hash"],
            )
            for row in rows
        ]
        previous_hash = ZERO_HASH
        chain_valid = True
        for row in all_rows:
            details = json.loads(row["details_json"])
            canonical = json.dumps(
                {
                    "timestamp": row["timestamp"],
                    "actor": row["actor"],
                    "action": row["action"],
                    "entity_type": row["entity_type"],
                    "entity_id": row["entity_id"],
                    "details": details,
                    "previous_hash": previous_hash,
                },
                sort_keys=True,
                separators=(",", ":"),
            )
            expected_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if row["previous_hash"] != previous_hash or row["event_hash"] != expected_hash:
                chain_valid = False
                break
            previous_hash = row["event_hash"]
        return events, len(all_rows), chain_valid

    def counts(self) -> dict[str, int]:
        with self.connect() as connection:
            return {
                "assessments": connection.execute("SELECT COUNT(*) FROM assessments").fetchone()[0],
                "cases": connection.execute("SELECT COUNT(*) FROM cases").fetchone()[0],
                "policies": connection.execute("SELECT COUNT(*) FROM policies").fetchone()[0],
                "audit_events": connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[
                    0
                ],
            }
