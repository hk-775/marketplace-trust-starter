# Ethics and responsible use

## Intended use

Marketplace Trust Starter demonstrates how a marketplace or community can
organize observable risk signals, policy controls, evidence, human review, and
audit without presenting a score as truth.

It is suitable for:

- product and architecture discussions;
- local prototyping;
- API and review-workflow integration tests;
- evaluation of explainability and operator experience;
- a starting point for jurisdiction-specific policy work.

It is not a deploy-and-forget moderation system.

## Prohibited uses

Do not use or extend this project to:

- infer race, ethnicity, religion, sex, gender identity, sexual orientation,
  disability, health, pregnancy, nationality, citizenship, or another
  protected or highly sensitive attribute;
- analyze faces, facial features, biometrics, skin tone, attractiveness,
  beauty, body shape, or personal appearance;
- rank people by desirability or social worth;
- use a score as proof of intent, criminality, fraud, or identity;
- automatically execute irreversible punitive action;
- conceal policy logic from affected operators or reviewers.

The API rejects prohibited input keys, including nested keys, before scoring.
The corresponding ethical-boundary policy is locked.

## Human review semantics

High and critical scores create cases. A case:

- identifies the source assessment;
- preserves its exact evidence snapshot;
- starts open and unassigned;
- must be claimed by a named reviewer;
- requires an explicit outcome and meaningful notes to resolve;
- cannot be changed after resolution through the API.

The reviewer may determine that a high score is a false positive. The seed data
includes that outcome intentionally.

## Precision-sensitive design

Ambiguous evidence is constrained:

- a URL alone is not malicious;
- a sparse profile alone remains low risk;
- reports provide capped supporting points;
- shared devices never trigger coordinated abuse alone;
- off-platform contact contributes only with new-account or scam context;
- direct-threat patterns avoid ordinary phrases such as “kill the process”;
- common safety-warning language suppresses scam and credential matches.

These choices favor precision over broad recall. They reduce harm from
unnecessary review, but they also mean novel or indirect abuse can be missed.

## Limitations

- Rules cannot determine intent.
- Regex and compound heuristics miss paraphrases and contextual meaning.
- Reports can be malicious, biased, duplicated, or brigaded.
- Shared devices can represent households, schools, libraries, or workplaces.
- Transaction history can disadvantage new participants.
- Policy tuning can create disparate outcomes even when protected attributes
  are not collected.
- Seed metrics do not establish production accuracy.

Every assessment repeats core limitations in its response.

## Before production use

At minimum:

1. Define written platform policy and appeal rights.
2. Consult legal, privacy, safety, and accessibility specialists.
3. Build representative, consented evaluation sets.
4. Measure false positives and false negatives by use case.
5. Test for proxy discrimination and disparate operational outcomes.
6. Establish report-abuse and coordinated-brigading defenses.
7. Minimize, encrypt, retain, and delete data under a documented schedule.
8. Train and support reviewers, including wellbeing practices.
9. Add authentication, authorization, tenant isolation, and rate limits.
10. Monitor policy changes and require approval for consequential thresholds.
11. Provide notice, explanation, correction, and appeal paths where applicable.
12. Keep irreversible decisions under accountable human authority.

## Adding a model

This starter ships no model. If a future adaptation adds one:

- document training and evaluation data provenance;
- separate model confidence from policy risk;
- calibrate on the host platform's actual distribution;
- test drift and subgroup outcomes without inferring attributes at runtime;
- retain deterministic fallback and explanation paths;
- fail safely when the model is unavailable;
- never introduce face or attractiveness scoring.

