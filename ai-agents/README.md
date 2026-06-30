# ai-agents/ — self-hosted LLM agent platforms

All apps share the external **`agents`** Docker network, sit behind the cloudflared
tunnel (`drawbridge`), and expose datastore metrics to Prometheus (`observatory`).
Each keeps its own private `<app>-internal` network.

> **Status: defined but STOPPED.** Authored for review — nothing here is running.
> Fill each `.env` (copy `.env.example`) before bringing one up.

| App | What | Local port | DB / deps | Metrics |
|-----|------|-----------|-----------|---------|
| [hermes](./hermes) | Open WebUI chat + homelab-control tool | 3025 | (none) | — |
| [flowise](./flowise) | Low-code LLM agent/chain builder | 8510 | Postgres | postgres_exporter |
| [langflow](./langflow) | Visual agent-flow builder | 8512 | Postgres | postgres_exporter |
| [librechat](./librechat) | Multi-provider chat UI | 8513 | MongoDB, Meilisearch | mongodb_exporter |
| [anythingllm](./anythingllm) | All-in-one private RAG/chat | 8514 | embedded | — |
| [dify](./dify) | LLM app platform (agents/workflows/RAG) | web 8511 / api 8519 | Postgres, Redis, Weaviate, sandbox | pg + redis exporters |

Local ports bind to `127.0.0.1` for testing; public access is via the tunnel
(`<app>.itproxima.com`).

## Observability
Exporters are scraped by Prometheus (`observatory/prometheus/prometheus.yml`) and
get auto-generated Grafana dashboards (PostgreSQL/Redis/MongoDB per-instance) from
`observatory/grafana/gen_dashboards.py`. Targets read **DOWN** until each stack starts.

## Apply one app
```bash
cd ai-agents/<app>
cp .env.example .env && $EDITOR .env
docker compose up -d
```

> **Volume permissions (langflow & anythingllm):** these images run as a non-root
> user (uid 1000) and write SQLite/secrets into their bind-mounted volume. A fresh
> root-owned `./volumes` makes them crash-loop (`unable to open database file` /
> `Permission denied: secret_key`). Fix before first start:
> ```bash
> mkdir -p ai-agents/langflow/volumes/data ai-agents/anythingllm/volumes/storage
> sudo chown -R 1000:1000 ai-agents/langflow/volumes ai-agents/anythingllm/volumes
> ```
