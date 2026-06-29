# Dashboards — Homepage, Dashy, Glance

Three dashboard options running simultaneously so you can pick your favourite. All three read the Docker socket to show live container status.

## Services

| Service | Port | URL | Best for |
|---|---|---|---|
| **Homepage** | 3002 | `home.yourdomain.com` | Rich service tiles with API integrations (Sonarr, Grafana stats, etc.) |
| **Dashy** | 4000 | `dash.yourdomain.com` | Visual bookmark board with status indicators |
| **Glance** | 8081 | `glance.yourdomain.com` | Feed reader + metrics overview on one scrollable page |

## Configuration

Each dashboard has its own config volume:
```
dashboards/
├── glance/config/glance.yml    — Glance layout and widgets
├── dashy/config/               — Dashy conf.yml
└── homepage/config/            — Homepage services.yaml, widgets.yaml, etc.
```

Edit the config files, then restart the relevant container — no image rebuild needed.

## Networks

Both `drawbridge` (public URLs) and `observatory` (monitoring) — all three containers.

## Bring up

```bash
docker compose up -d
```

All three start together. Bring down any one individually with:
```bash
docker compose stop homepage   # or dashy, or glance
```
