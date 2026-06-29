# Observatory — Metrics, Logs, and Dashboards

Full observability stack. Every container in the homelab is scraped by Prometheus, every log line is shipped to Loki, and Grafana ties it together into dashboards.

## Stack

```
prometheus      — time-series metrics store (15-day retention)
grafana         — dashboards, alerting, Loki log explorer
loki            — log aggregation backend
promtail        — log collector (Docker socket + host log files)
node-exporter   — host-level metrics: CPU, RAM, disk, network
cadvisor        — per-container resource metrics
```

All per-service exporters (Postgres, Redis, CouchDB) live alongside their respective stacks but report into the `observatory` network — Prometheus scrapes them all from one place.

## Scrape targets

| Target | What it exports |
|---|---|
| `node-exporter` | Host CPU, RAM, disk I/O, network, filesystem |
| `cadvisor` | Per-container CPU, RAM, network, disk (all running containers) |
| `n8n-main`, `n8n-worker{1,2,3}` | Workflow executions, queue depth, API latency |
| `n8n-postgres-exporter` | n8n DB connections, query stats, table sizes |
| `n8n-redis-exporter` | n8n queue Redis: memory, commands/sec, keyspace |
| `evo-postgres-exporter` | Evolution API DB metrics |
| `evo-redis-exporter` | Evolution API Redis metrics |
| `automation-postgres-exporter` | Business-process DB metrics |
| `couchdb-exporter` | CouchDB: doc counts, disk sizes per database (vault health) |
| `cloudflared` | Tunnel metrics: active connections, request rates |

## Networks

| Network | Why |
|---|---|
| `observatory` | All monitoring containers live here; every scrape target joins this network |
| `drawbridge` | Grafana only — gives it a public URL at `grafana.yourdomain.com` |

## Log shipping

Promtail collects from two sources:
1. **Docker socket** — all container stdout/stderr, labelled by container name and stack
2. **`/var/log/homelab/`** — host-side cron job logs (vault→GitHub sync, rclone jobs)

Labels on every log stream: `container`, `host`, `job`. Filter in Grafana Explore with:
```
{container="n8n-main"} |= "error"
{job="vault-push"} | json
```

## Grafana provisioning

Datasources (Prometheus, Loki) and dashboards are provisioned from:
```
grafana/provisioning/   — datasources and dashboard folders
grafana/dashboards/     — JSON dashboard files
```

Drop a new dashboard JSON into `grafana/dashboards/` and restart Grafana — it appears automatically.

## Environment

Create `observatory/monitoring/.env`:
```
GF_SECURITY_ADMIN_PASSWORD=<strong password>
```

## Bring up

```bash
docker compose up -d
```

Grafana is available at `http://localhost:3000` locally and `grafana.yourdomain.com` via the tunnel.

## Retention

Prometheus: 15 days (`--storage.tsdb.retention.time=15d` in the compose command). Adjust in `docker-compose.yml` based on your disk budget. A typical homelab at this scale generates ~500 MB of TSDB data per month.
