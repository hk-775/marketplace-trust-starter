# Meeting-ready demo guide

## Preparation

From the project root:

```bash
./scripts/demo.sh
```

Confirm:

```bash
python scripts/smoke_test.py --base-url http://127.0.0.1:8101
```

The smoke test restores seed state before it exits.

## Eight-minute walkthrough

### 1. Product boundary — 1 minute

Open `http://127.0.0.1:8101`.

Emphasize:

- deterministic and explainable;
- local and credential-free;
- behavior rather than identity or appearance;
- score routes work and never proves abuse;
- no irreversible automated enforcement.

### 2. Operations overview — 1 minute

Open `/dashboard`.

Show:

- 10 seeded assessments;
- 4 active review cases;
- all four risk tiers;
- policy version;
- recent assessment evidence.

All names and identifiers are fictional.

### 3. Guided scenario — 2 minutes

Open **Guided demo** and run **Gift-card solicitation**.

Point out:

- financial solicitation requires instrument plus action;
- off-platform movement needs risk context;
- repetition and reports are separate supporting signals;
- the score is a sum of visible points;
- the result creates a case rather than an enforcement action.

Run **Sparse new profile** to demonstrate a weak signal staying below review.

### 4. Human review — 2 minutes

Open **Review queue**.

1. Claim the newly created case as `Demo Operator`.
2. Resolve it with an explicit outcome and notes.
3. Explain that direct `open → resolved` is rejected.
4. Show the seeded false-positive case for `cluster-workshop`.

### 5. Policy and audit — 1 minute

Open **Policy controls**.

- Show editable signal controls.
- Show locked human-review and ethical boundaries.
- Edit an unlocked weight with a reason.

Open **Audit trail** and show the verified chain and policy event.

### 6. Architecture and reset — 1 minute

Open `/architecture` and play the human-review flow.

Return to the dashboard, select **Reset seed**, type `RESET DEMO`, and restore
the canonical state.

## Scenario expectations

| Scenario | Expected result | Teaching point |
|---|---|---|
| Ordinary local listing | Low | Positive history and no risky rule |
| Gift-card solicitation | High or critical | Compound content and behavior evidence |
| Coordinated listing burst | Critical | Multiple independent coordination signals |
| Sparse new profile | Low | One weak signal does not create a case |

Policy edits can change exact scores, which is why each assessment records its
policy version.

## Presenter cautions

Do not describe:

- the score as fraud probability;
- the rules as comprehensive detection;
- the seed outcomes as accuracy validation;
- SQLite as a production shared datastore;
- the static dashboard as a live API;
- the starter as compliant with a particular law or marketplace policy.

