# API guide

Base URL:

```text
http://127.0.0.1:8101
```

Interactive OpenAPI documentation:

```text
http://127.0.0.1:8101/api/docs
```

All request bodies are JSON. Unknown fields are rejected.

## Health

```http
GET /api/v1/health
```

Returns service version, mode, storage, seed counts, external-network posture,
and ethical boundaries.

## Assess a profile

```http
POST /api/v1/assess/profile
Content-Type: application/json
```

```json
{
  "subject_id": "profile-104",
  "bio": "Neighborhood ceramicist.",
  "account_age_days": 240,
  "profile_completeness": 0.9,
  "verified_contact": true,
  "media_count": 5,
  "outbound_messages_1h": 2,
  "unique_recipients_1h": 2,
  "bio_reuse_count_7d": 0,
  "linked_accounts_30d": 0,
  "prior_reports_30d": 0,
  "successful_transactions_90d": 12,
  "chargebacks_90d": 0
}
```

## Assess content

```http
POST /api/v1/assess/content
Content-Type: application/json
```

```json
{
  "subject_id": "seller-204",
  "content_id": "listing-882",
  "content_type": "listing",
  "text": "Oak side table, local pickup.",
  "account_age_days": 120,
  "previous_similar_posts_1h": 0,
  "unique_recipients_1h": 1,
  "reports_24h": 0,
  "successful_transactions_90d": 8
}
```

`content_type` is one of `message`, `listing`, `post`, or `comment`.

## Assess coordinated abuse

```http
POST /api/v1/assess/coordinated-abuse
Content-Type: application/json
```

```json
{
  "cluster_id": "cluster-31",
  "participating_accounts": 12,
  "new_account_ratio": 0.82,
  "duplicate_content_ratio": 0.88,
  "shared_device_ratio": 0.7,
  "events_10m": 160,
  "target_concentration": 0.74,
  "independent_reports": 6,
  "established_account_ratio": 0.1
}
```

## Assessment response

Important fields:

- `risk_score`: bounded 0–100 review-priority score;
- `risk_tier`: `low`, `guarded`, `high`, or `critical`;
- `confidence`: confidence in available evidence, not probability of guilt;
- `signals`: positive point contributions;
- `counter_signals`: negative point contributions;
- `policy_version`: policy snapshot used;
- `requires_human_review`: whether a case was created;
- `case_id`: case identifier or `null`;
- `limitations`: required interpretation warnings.

Each signal includes `signal_id`, category, label, description, base points,
multiplier, final points, and evidence.

## List assessments

```http
GET /api/v1/assessments?limit=50
```

## Review cases

List:

```http
GET /api/v1/cases?status=open&limit=100
```

Read one:

```http
GET /api/v1/cases/C-2002
```

Claim:

```http
PATCH /api/v1/cases/C-2002
Content-Type: application/json

{
  "status": "in_review",
  "reviewer": "Jordan Lee"
}
```

Resolve:

```http
PATCH /api/v1/cases/C-2002
Content-Type: application/json

{
  "status": "resolved",
  "reviewer": "Jordan Lee",
  "outcome": "false_positive",
  "resolution_notes": "The repeated post was an approved community workshop notice."
}
```

Outcomes:

- `confirmed_abuse`
- `false_positive`
- `insufficient_evidence`
- `no_action`

An open case cannot resolve directly, and a resolved case is terminal.

## Metrics and insights

```http
GET /api/v1/metrics
GET /api/v1/insights
```

Metrics include queue depth, tier and status distributions, median score,
high/critical rate, review outcomes, and policy version.

Insights identify the engine as deterministic, list active signals and average
points, show counter-signal hits, and repeat responsible-use safeguards.

## Policy controls

List:

```http
GET /api/v1/policies
```

Update an editable rule:

```http
PATCH /api/v1/policies/content_spam_burst
Content-Type: application/json

{
  "weight": 0.8,
  "threshold": 30,
  "actor": "Policy Operator",
  "reason": "Evaluate a more conservative burst threshold in the local demo"
}
```

At least one of `enabled`, `weight`, or `threshold` is required. Locked
governance and ethical boundaries return `409`.

## Audit

```http
GET /api/v1/audit?limit=100
```

Returns newest events first plus `total` and `chain_valid`.

## Guided demo and reset

```http
GET /api/v1/demo/scenarios
POST /api/v1/demo/scenarios/gift-card-scam
```

Reset all mutable local state:

```http
POST /api/v1/demo/reset
Content-Type: application/json

{
  "actor": "demo-operator",
  "confirmation": "RESET DEMO"
}
```

## Validation errors

FastAPI returns `422` for malformed or prohibited input. Review-state conflicts
and locked policy changes return `409`. Missing entities return `404`.

Protected-attribute, biometric, face, attractiveness, beauty, and appearance
fields are prohibited even when nested.

