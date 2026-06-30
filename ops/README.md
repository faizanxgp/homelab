# ops/ — operate the homelab

`homelab.sh` auto-discovers every Compose stack (no hardcoded list) and manages them:

```bash
ops/homelab.sh list      # every stack + running/stopped
ops/homelab.sh config    # validate every docker-compose.yml (docker compose config -q)
ops/homelab.sh ps        # running containers
ops/homelab.sh up   marketing/umami
ops/homelab.sh down marketing/umami
```

## Topology (post-reorg)

| Folder | Network(s) | Stacks |
|--------|-----------|--------|
| `automation/` | `automation` | n8n, evoapi, postgres (automation-postgres), textbee (textbee-mongo) |
| `marketing/` | `marketing` | postiz (+temporal-postgres/es exporters), listmonk, umami, matomo, metabase, typebot, chatwoot, plausible, posthog |
| `ai-agents/` | `agents` | hermes, flowise, langflow, librechat, anythingllm, dify |
| `sites/` | `sites` | obsidian, uploads, downloads, apk-server, tavern |
| `observatory/` | `observatory` | prometheus, grafana, loki, promtail, node-exporter, cadvisor, **dozzle**, uptime-kuma |
| `dashboards/` | — | dashy, glance, homepage, **beszel** |
| `utility/` | — | cloudflared, couchdb, db-viewer, webdav, claude-code |

All stacks join `observatory` for metrics/logs and `drawbridge` (cloudflared) where public.

## Currently STOPPED (review before starting)

Decommissioned/standby this session (volumes preserved, fully reversible):
`postiz · hermes · obsidian · uploads · downloads · apk-server · sillytavern ·
db-viewer · couchdb · snippetbox · dashy · glance · homepage`

Brand-new and **never started** (RAM): the whole `marketing/` and `ai-agents/`
stacks, plus `observatory/dozzle` and `dashboards/beszel`. The heaviest are
**posthog** (ClickHouse+Kafka+MinIO) and **dify** (Weaviate+sandbox) — size the box first.

## Start a new stack
```bash
cd <folder>/<stack>
cp .env.example .env && $EDITOR .env   # fill secrets
docker compose up -d
```
External networks (`marketing`, `sites`, `agents`) already exist. Recreate any with
`docker network create <name>` if needed.
