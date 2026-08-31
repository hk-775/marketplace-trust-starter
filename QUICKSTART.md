# Quick start

## Option 1: complete local demo

Requirements:

- Python 3.11–3.13
- `uv` 0.10.7 or newer
- a shell capable of running Bash scripts

Start:

```bash
./scripts/demo.sh
```

Expected URLs:

| Experience | URL |
|---|---|
| Landing page | `http://127.0.0.1:8101` |
| Dashboard | `http://127.0.0.1:8101/dashboard` |
| Architecture | `http://127.0.0.1:8101/architecture` |
| OpenAPI | `http://127.0.0.1:8101/api/docs` |

The first start creates `data/marketplace_trust_starter.db` and seeds fictional
demo state. Stop with `Ctrl-C`; restart with the same command.

The script synchronizes the committed `uv.lock` and launches the console entry
point with `uv run --locked`. Dependency installation may contact the
configured Python package index. The running product requires no credentials
and makes no external service calls.

## Five-minute product walkthrough

1. Open the landing page and review the responsible-use boundary.
2. Open the dashboard. Confirm the seeded KPIs and tier distribution.
3. Select **Guided demo** and run **Gift-card solicitation**.
4. Note the named signals, point contributions, policy version, and new case.
5. Open **Review queue**, claim the case, then resolve it with an outcome and
   notes.
6. Open **Audit trail** and confirm the chain remains verified.
7. Open **Policy controls**, edit an unlocked rule with a reason, and run a new
   assessment.
8. Use **Reset seed** and type `RESET DEMO` to restore the canonical state.

## Try the API

Health:

```bash
curl http://127.0.0.1:8101/api/v1/health
```

Benign listing:

```bash
curl -X POST http://127.0.0.1:8101/api/v1/assess/content \
  -H 'Content-Type: application/json' \
  -d '{
    "subject_id": "quickstart-seller",
    "content_id": "quickstart-listing",
    "content_type": "listing",
    "text": "Small oak table available for local pickup.",
    "account_age_days": 420,
    "successful_transactions_90d": 16
  }'
```

Reset:

```bash
curl -X POST http://127.0.0.1:8101/api/v1/demo/reset \
  -H 'Content-Type: application/json' \
  -d '{"actor":"quickstart","confirmation":"RESET DEMO"}'
```

## Option 2: Docker Compose

```bash
docker compose up --build
```

The app listens on host port `8101` and stores SQLite state in the named
`marketplace_trust_data` volume.

To stop:

```bash
docker compose down
```

To remove the demo volume as well, explicitly run:

```bash
docker compose down --volumes
```

That final command deletes the Docker-managed demo database.

## Alternate host binding

The canonical service port remains `8101`. To map a different host port in
Compose:

```bash
MTS_HOST_PORT=18101 docker compose up --build
```

For the local Python process:

```bash
MTS_PORT=8101 MTS_HOST=0.0.0.0 ./scripts/demo.sh
```

Binding beyond `127.0.0.1` exposes an unauthenticated demonstration service.
Do not do so on an untrusted network.
