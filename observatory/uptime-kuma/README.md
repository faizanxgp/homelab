# Uptime Kuma — Service Availability Monitor

Beautiful, self-hosted uptime monitor. Pings your services on a schedule and gives you a public status page, push notifications, and a historical uptime record.

## What to monitor

Add monitors for each public-facing service. Suggested setup:

| Monitor | Type | URL |
|---|---|---|
| n8n | HTTP(s) | `https://n8n.yourdomain.com/healthz` |
| Evolution API | HTTP(s) | `https://evolution.yourdomain.com/` |
| Grafana | HTTP(s) | `https://grafana.yourdomain.com/api/health` |
| CouchDB | HTTP(s) | `https://couch.yourdomain.com/_up` |
| Obsidian | HTTP(s) | `https://obsidian.yourdomain.com/` |
| Downloads | HTTP(s) | `https://downloads.yourdomain.com/` |

## Networks

| Network | Why |
|---|---|
| `observatory` | Monitoring plane membership |
| `drawbridge` | Public URL at `uptime.yourdomain.com` |

## Bring up

```bash
docker compose up -d
```

Data persists in `./volumes/data/`. First run opens a setup wizard for the admin account.
