# 🧰 Cool dockers & apps to add next

Curated, high-signal self-hosted services that fit this homelab (Docker +
cloudflared tunnel + observatory monitoring). Ordered by bang-for-buck. Each is a
single `docker compose up` in a new `utility/<name>/` folder + one route in
`deploy-tunnel.sh` (the established pattern).

## 🔝 Add these first (highest value)
| App | What it gives you | Why it's worth it |
|---|---|---|
| **Vaultwarden** | Self-hosted Bitwarden password manager | Own your secrets; killer portfolio piece; you have *lots* of creds to wrangle |
| **Dozzle** | Real-time Docker logs in the browser | See every container's logs without `docker logs`; pairs with Uptime Kuma |
| **Ntfy** | Dead-simple push notifications (phone) | Wire load-shedding alerts, deploy/CI pings, Uptime Kuma down-alerts to your phone |
| **NocoDB** / **Baserow** | Airtable-style DB UI over Postgres | No-code data app on top of your existing Postgres; great for marketing data |
| **Beszel** or **Glances** | Lightweight server/agent monitoring | Slick resource dashboards beyond Grafana; Beszel is gorgeous |

## 🤖 AI / agents (the "like Hermes" family)
| App | What it gives you |
|---|---|
| **Flowise** | Visual LLM agent/flow builder (drag-drop chains, RAG, tools) |
| **Dify** | Full LLMOps platform — build + host AI apps, RAG, agents, datasets |
| **Langflow** | Another visual agent builder (LangChain-based) |
| **SearXNG** + **Perplexica** | Private meta-search + an AI "Perplexity" answer engine over it |
| **LibreChat** | Multi-model chat with MCP/agents/code-interpreter (alt to Hermes) |
| **Activepieces** / **Windmill** | AI-friendly automation (n8n alternatives) for scripts + flows |

## 🗂️ Productivity / "own your life"
| App | What it gives you |
|---|---|
| **Immich** | Self-hosted Google Photos (AI face/object search) |
| **Paperless-ngx** | Scan→OCR→searchable document archive |
| **Karakeep** (Hoarder) | AI-tagged bookmark/read-later with full-text search |
| **Actual Budget** | Private envelope-budgeting (great for the "desi saver" in you) |
| **Stirling-PDF** | Every PDF operation in one UI |
| **Mealie** | Recipe manager + meal planner |

## 🛠️ Dev / platform
| App | What it gives you |
|---|---|
| **Coolify** / **Dokploy** | Self-hosted Heroku/Vercel — deploy apps with a click (huge portfolio flex) |
| **Gitea** / **Forgejo** | Your own GitHub (mirror repos, run Actions) |
| **Portainer** | Full Docker management GUI |
| **Registry + UI** | Private container registry |

## 📊 Data / dashboards (marketing-interview relevant)
| App | What it gives you |
|---|---|
| **Metabase** | No-code BI dashboards over any DB (see `utility/postiz/marketing-arsenal.md`) |
| **PostHog** | Product analytics: funnels, cohorts, session replay, A/B, flags |
| **Umami** / **Matomo** | Privacy-first web analytics (GA replacement) |
| **Listmonk** | Self-hosted newsletter + campaign analytics |

## 📺 Media (optional fun)
**Jellyfin** (media server), **Navidrome** (music), **FreshRSS**/**Miniflux** (RSS),
**Wallabag** (read-later).

---
*Tell Hermes (or me) which row to deploy and it's one compose + one route away.*
