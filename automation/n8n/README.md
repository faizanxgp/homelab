# n8n — Queue-Mode Automation Engine

Production-grade n8n deployment: main process + **3 workers** backed by Postgres 16 and Redis 7. Handles webhooks, schedules, and heavy workflows simultaneously without any execution blocking.

## Architecture

```
n8n-main      — webhook receiver, UI, API (port 5678 → drawbridge → tunnel)
n8n-worker    ─┐
n8n-worker-2  ─┤  pull jobs from Redis Bull queue, execute workflows
n8n-worker-3  ─┘
n8n-postgres  — persistent workflow/execution storage (Postgres 16)
n8n-redis     — Bull job queue + cache (Redis 7, AOF persistence)
```

**Why queue mode?** In the default single-process mode, long-running workflows block webhook responses. Queue mode separates triggering (main) from executing (workers) — three simultaneous heavy workflows never starve each other.

## Networks

| Network | Why |
|---|---|
| `automation` | Internal: workers, Postgres, Redis all talk here |
| `drawbridge` | n8n-main only — gives it a public URL via the tunnel |
| `observatory` | All containers — Prometheus scrapes `/metrics` on each |

## Metrics

Full Prometheus metrics are enabled on n8n-main and each worker:

- Workflow execution counts, durations, success/failure rates
- Queue depth and worker throughput
- Cache hit rates, API endpoint latency
- Postgres and Redis via dedicated exporters (`n8n-postgres-exporter`, `n8n-redis-exporter`)

## Environment

| Variable | Purpose |
|---|---|
| `N8N_DB_PASSWORD` | Postgres password (shared between n8n and its Postgres) |
| `N8N_ENCRYPTION_KEY` | Encrypts stored credentials at rest — **never change after first run** |

Generate a secure encryption key once:
```bash
openssl rand -base64 32
```

> If you change `N8N_ENCRYPTION_KEY` after credentials are stored, all stored credentials become unreadable.

## Bring up

```bash
cp .env.example .env
# edit .env with strong values
docker compose up -d
```

Health checks on Postgres and Redis must pass before n8n starts. The compose file uses `depends_on: condition: service_healthy`.

## Scaling workers

To add a fourth worker, copy the `n8n-worker-3` block in `docker-compose.yml` and rename it `n8n-worker-4`. Workers are stateless — you can scale up or down without downtime.

## Upgrade

```bash
docker compose pull
docker compose up -d
```

n8n runs database migrations automatically on startup. Back up Postgres before major version jumps.
