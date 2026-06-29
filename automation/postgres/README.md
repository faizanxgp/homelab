# automation-postgres — Business-Process Database

Standalone Postgres 16 instance for application data built by n8n workflows — separate from n8n's own operational database. Think of it as the "output" database: your automations write structured business data here (contacts, events, logs, whatever your workflows produce).

## Why a separate Postgres?

n8n has its own internal Postgres for storing workflows and execution history. This instance is for **your data** — the records your automations create. Keeping them separate means:

- n8n upgrades and migrations don't touch your application schema
- You can wipe n8n's DB to start fresh without losing your data
- Access control is independent — this DB can be locked down differently

## Access

The DB is on the `automation` network only — not on `drawbridge`. To inspect it via a web UI, bring up the `db-viewer` stack:

```bash
docker compose -f /opt/homelab/utility/db-viewer/docker-compose.yml up -d
# Open db.yourdomain.com (Cloudflare Access gated)
# Tear down when done:
docker compose -f /opt/homelab/utility/db-viewer/docker-compose.yml down
```

## Environment

| Variable | Purpose |
|---|---|
| `AUTOMATION_DB_PASSWORD` | Postgres password |

## Bring up

```bash
cp .env.example .env
docker compose up -d
```

## Prometheus metrics

A `postgres-exporter` sidecar scrapes this instance and exposes metrics to the `observatory` network. Tables sizes, connection counts, and query stats appear in Grafana automatically once Prometheus is scraping.
