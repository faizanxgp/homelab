#!/usr/bin/env python3
"""Provision Uptime Kuma monitors for the whole homelab + a pretty, boxed status
page (idempotent).

Usage:  python3 provision-monitors.py 'KUMA_ADMIN_PASSWORD'

What it does
------------
1. Creates four monitor groups (Public Edge / Internal Apps / Databases / Containers)
   and fills them with HTTP, TCP-port and Docker-state monitors covering the current
   topology: core automation, the marketing stack, the ai-agents stack, observability
   and the sites stack.
2. Builds/refreshes a public **status page** (`homelab`) that arranges everything into
   per-stack sections rendered as a responsive card grid (custom CSS) instead of one
   long flat list.

Add-only & idempotent: re-running never duplicates monitors. Services that are
currently stopped simply show DOWN until you start them (pause them in Kuma if you
prefer a clean board).
"""
import sys
from uptime_kuma_api import UptimeKumaApi, MonitorType

PW = sys.argv[1]
HTTP_CODES = ["200-299", "300-399", "400-499"]  # refused/timeout/5xx => DOWN
INTERVAL = 60
STATUS_SLUG = "homelab"

# ── Web URL pings: full edge DNS -> Cloudflare -> tunnel -> app ────────────────
PUBLIC = [
    # core automation
    ("n8n",            "https://n8n.itproxima.com/"),
    ("Evolution API",  "https://evolution.itproxima.com/"),
    ("TextBee",        "https://text.itproxima.com/"),
    # observability
    ("Grafana",        "https://grafana.itproxima.com/"),
    ("Uptime Kuma",    "https://uptime.itproxima.com/"),
    ("Dozzle",         "https://dozzle.itproxima.com/"),
    ("Beszel",         "https://beszel.itproxima.com/"),
    # marketing
    ("Postiz",         "https://postiz.itproxima.com/"),
    ("Listmonk",       "https://listmonk.itproxima.com/"),
    ("Umami",          "https://umami.itproxima.com/"),
    ("Matomo",         "https://matomo.itproxima.com/"),
    ("Metabase",       "https://metabase.itproxima.com/"),
    ("Typebot",        "https://typebot.itproxima.com/"),
    ("Chatwoot",       "https://chatwoot.itproxima.com/"),
    ("Plausible",      "https://plausible.itproxima.com/"),
    ("PostHog",        "https://posthog.itproxima.com/"),
    # ai-agents
    ("Hermes",         "https://hermes.itproxima.com/"),
    ("Flowise",        "https://flowise.itproxima.com/"),
    ("Langflow",       "https://langflow.itproxima.com/"),
    ("LibreChat",      "https://librechat.itproxima.com/"),
    ("AnythingLLM",    "https://anythingllm.itproxima.com/"),
    ("Dify",           "https://dify.itproxima.com/"),
    # sites
    ("Obsidian",       "https://obsidian.itproxima.com/"),
    ("Uploads",        "https://uploads.itproxima.com/"),
    ("Downloads",      "https://downloads.itproxima.com/"),
    ("APK server",     "https://apk.itproxima.com/"),
    ("SillyTavern",    "https://tavern.itproxima.com/"),
    ("WebDAV",         "https://dav.itproxima.com/"),
]

# ── Internal app health by container name on the observatory network ───────────
INTERNAL = [
    ("n8n (main)",      "http://n8n-main:5678/healthz"),
    ("Evolution API",   "http://evolution-api:8080/"),
    ("TextBee API",     "http://textbee-api:3001/"),
    ("TextBee Web",     "http://textbee-web:3000/"),
    ("Grafana",         "http://grafana:3000/api/health"),
    ("Prometheus",      "http://prometheus:9090/-/healthy"),
    ("Loki",            "http://loki:3100/ready"),
    ("Dozzle",          "http://dozzle:8080/"),
    ("Beszel",          "http://beszel:8090/"),
    ("WebDAV",          "http://webdav:6065/"),
    # marketing
    ("Postiz",          "http://postiz:5000/"),
    ("Listmonk",        "http://listmonk:9000/"),
    ("Umami",           "http://umami:3000/api/heartbeat"),
    ("Matomo",          "http://matomo:80/"),
    ("Metabase",        "http://metabase:3000/api/health"),
    ("Typebot Builder", "http://typebot-builder:3000/"),
    ("Typebot Viewer",  "http://typebot-viewer:3000/"),
    ("Chatwoot",        "http://chatwoot-web:3000/"),
    ("Plausible",       "http://plausible:8000/api/health"),
    ("PostHog",         "http://posthog-web:8000/_health"),
    # ai-agents
    ("Hermes",          "http://hermes:8080/"),
    ("Flowise",         "http://flowise:3000/"),
    ("Langflow",        "http://langflow:7860/health"),
    ("LibreChat",       "http://librechat:3080/"),
    ("AnythingLLM",     "http://anythingllm:3001/api/ping"),
    ("Dify Web",        "http://dify-web:3000/"),
    ("Dify API",        "http://dify-api:5001/health"),
    # sites
    ("Obsidian",        "http://obsidian:3000/"),
    ("Uploads",         "http://uploads:80/"),
    ("Downloads",       "http://downloads:80/"),
    ("APK server",      "http://apk-server:80/"),
    ("SillyTavern",     "http://sillytavern:8000/"),
]

# ── Datastore TCP-port checks (no creds stored) ───────────────────────────────
DBS = [
    # core
    ("Postgres - n8n",          "n8n-postgres",        5432),
    ("Postgres - Evolution",    "evo-postgres",        5432),
    ("Postgres - automation",   "automation-postgres", 5432),
    ("Redis - n8n",             "n8n-redis",           6379),
    ("Redis - Evolution",       "evo-redis",           6379),
    ("Redis - TextBee",         "textbee-redis",       6379),
    ("MongoDB - TextBee",       "textbee-mongo",       27017),
    # marketing
    ("Postgres - listmonk",     "listmonk-db",         5432),
    ("Postgres - umami",        "umami-db",            5432),
    ("MariaDB - matomo",        "matomo-db",           3306),
    ("Postgres - metabase",     "metabase-db",         5432),
    ("Postgres - typebot",      "typebot-db",          5432),
    ("Postgres - chatwoot",     "chatwoot-postgres",   5432),
    ("Redis - chatwoot",        "chatwoot-redis",      6379),
    ("Postgres - plausible",    "plausible-db",        5432),
    ("Postgres - posthog",      "posthog-db",          5432),
    ("Redis - posthog",         "posthog-redis",       6379),
    # ai-agents
    ("Postgres - flowise",      "flowise-db",          5432),
    ("Postgres - langflow",     "langflow-db",         5432),
    ("MongoDB - librechat",     "librechat-mongo",     27017),
    ("Postgres - dify",         "dify-db",             5432),
    ("Redis - dify",            "dify-redis",          6379),
]

# ── Endpoint-less services: monitor the Docker container running-state ─────────
CONTAINERS = [
    "promtail", "cloudflared", "node-exporter", "cadvisor",
    "n8n-postgres-exporter", "n8n-redis-exporter",
    "evo-postgres-exporter", "evo-redis-exporter",
    "automation-postgres-exporter",
    "textbee-mongo-exporter", "textbee-redis-exporter",
    # marketing infra (postiz + temporal)
    "postiz-postgres", "postiz-redis",
    "postiz-postgres-exporter", "postiz-redis-exporter",
    "temporal", "temporal-postgres", "temporal-elasticsearch",
    "temporal-postgres-exporter", "temporal-es-exporter",
]
DOCKER_HOST_NAME = "local-socket"
DOCKER_SOCK = "/var/run/docker.sock"

api = UptimeKumaApi("http://127.0.0.1:3001")
api.login("faizanxgp", PW)

existing = {m["name"]: m for m in api.get_monitors()}
NAME2ID = {}  # full monitor name -> id (for the status page)


def _remember(name, mid):
    NAME2ID[name] = mid


def ensure_group(name):
    if name in existing:
        return existing[name]["id"]
    mid = api.add_monitor(type=MonitorType.GROUP, name=name)["monitorID"]
    existing[name] = {"id": mid, "name": name}
    print(f"  + group {name} (#{mid})")
    return mid


def ensure_http(name, url, parent):
    full = f"{name} :: {url}"
    if full in existing:
        _remember(full, existing[full]["id"] if isinstance(existing[full], dict) else None)
        return
    mid = api.add_monitor(type=MonitorType.HTTP, name=full, url=url, parent=parent,
                          interval=INTERVAL, accepted_statuscodes=HTTP_CODES,
                          maxredirects=10)["monitorID"]
    existing[full] = {"id": mid, "name": full}
    _remember(full, mid)
    print(f"    + {full}")


def ensure_port(name, host, port, parent):
    full = f"{name} :: {host}:{port}"
    if full in existing:
        _remember(full, existing[full]["id"] if isinstance(existing[full], dict) else None)
        return
    mid = api.add_monitor(type=MonitorType.PORT, name=full, hostname=host, port=port,
                          parent=parent, interval=INTERVAL)["monitorID"]
    existing[full] = {"id": mid, "name": full}
    _remember(full, mid)
    print(f"    + {full}")


def ensure_docker_host():
    for h in api.get_docker_hosts():
        if h.get("name") == DOCKER_HOST_NAME:
            return h["id"]
    r = api.add_docker_host(name=DOCKER_HOST_NAME, dockerType="socket",
                            dockerDaemon=DOCKER_SOCK)
    hid = (r or {}).get("id") or (r or {}).get("dockerHostID")
    if hid is None:
        for h in api.get_docker_hosts():
            if h.get("name") == DOCKER_HOST_NAME:
                hid = h["id"]; break
    print(f"  + docker host {DOCKER_HOST_NAME} (#{hid})")
    return hid


def ensure_docker(container, host_id, parent):
    full = f"{container} :: container"
    if full in existing:
        _remember(full, existing[full]["id"] if isinstance(existing[full], dict) else None)
        return
    mid = api.add_monitor(type=MonitorType.DOCKER, name=full, parent=parent,
                          interval=INTERVAL, docker_container=container,
                          docker_host=host_id)["monitorID"]
    existing[full] = {"id": mid, "name": full}
    _remember(full, mid)
    print(f"    + {full}")


# ── A boxed, per-stack status page ────────────────────────────────────────────
# Renders each Kuma group's monitor list as a responsive card grid with a gradient
# header — turning the default single long list into "fancy boxes".
STATUS_CSS = """
:root { --hl-accent:#7c5cff; --hl-accent2:#22d3ee; --hl-card:#161b2e; }
.status-page-body, body { background:
  radial-gradient(1200px 600px at 10% -10%, rgba(124,92,255,.18), transparent),
  radial-gradient(1000px 500px at 110% 10%, rgba(34,211,238,.15), transparent),
  #0b0f1c !important; }
.shadow-box, .status-page .container { background: transparent !important; box-shadow:none !important; }
h1.mb-1 { font-weight:800; letter-spacing:.5px;
  background:linear-gradient(90deg,var(--hl-accent),var(--hl-accent2));
  -webkit-background-clip:text; background-clip:text; -webkit-text-fill-color:transparent; }
.description span, .description p { color:#9aa4c4 !important; }
/* group heading -> pill */
.group-title, .item-name + .mt-3, .monitor-list .list-header, h2, .mb-4 > h2 {
  font-weight:700; }
.mb-4 > .my-3, .group .group-title { display:inline-block; padding:.25rem .9rem;
  border-radius:999px; background:linear-gradient(90deg, rgba(124,92,255,.25), rgba(34,211,238,.18));
  border:1px solid rgba(124,92,255,.35); margin-bottom:.6rem; }
/* monitor list -> responsive card grid */
.monitor-list { display:grid !important;
  grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:14px; }
.monitor-list .item { background:var(--hl-card) !important;
  border:1px solid rgba(124,92,255,.18); border-radius:16px; padding:14px 16px !important;
  transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease;
  box-shadow:0 6px 18px rgba(0,0,0,.35); }
.monitor-list .item:hover { transform:translateY(-3px);
  border-color:var(--hl-accent); box-shadow:0 12px 28px rgba(124,92,255,.25); }
.monitor-list .item .info { gap:.35rem; }
.monitor-list .item .badge { border-radius:999px; font-weight:600; }
/* uptime pills & heartbeat bar */
.hp-bar-big .beat { border-radius:3px !important; }
.dropdown-menu { border-radius:14px; }
"""


def build_status_page(groups):
    """groups: ordered list of (section_title, [monitor_id, ...])."""
    slugs = [s["slug"] for s in api.get_status_pages()]
    if STATUS_SLUG not in slugs:
        api.add_status_page(STATUS_SLUG, "Homelab Status")
        print(f"  + status page /{STATUS_SLUG}")
    public_group_list = []
    for w, (title, ids) in enumerate(groups, start=1):
        ids = [i for i in ids if i]
        if not ids:
            continue
        public_group_list.append({
            "name": title, "weight": w,
            "monitorList": [{"id": i} for i in ids],
        })
    api.save_status_page(
        STATUS_SLUG,
        title="Homelab Status",
        description="Live health of the homelab — automation, marketing, AI agents, observability.",
        theme="dark",
        published=True,
        showPoweredBy=False,
        customCSS=STATUS_CSS,
        footerText="itproxima homelab · auto-provisioned",
        publicGroupList=public_group_list,
    )
    print(f"  ~ status page saved with {len(public_group_list)} sections")


def ids_for(prefixes):
    """Collect monitor ids whose friendly name starts with any given prefix."""
    out = []
    for full, mid in NAME2ID.items():
        label = full.split(" :: ")[0]
        if any(label == p or label.startswith(p) for p in prefixes):
            out.append(mid)
    return out


try:
    g_pub = ensure_group("🌐 Public Edge")
    for n, u in PUBLIC:
        ensure_http(n, u, g_pub)
    g_int = ensure_group("🧩 Internal Apps")
    for n, u in INTERNAL:
        ensure_http(n, u, g_int)
    g_db = ensure_group("🗄️ Databases")
    for n, h, p in DBS:
        ensure_port(n, h, p, g_db)
    g_ctr = ensure_group("🐳 Containers (no endpoint)")
    host_id = ensure_docker_host()
    for c in CONTAINERS:
        ensure_docker(c, host_id, g_ctr)
    print("TOTAL monitors now:", len(api.get_monitors()))

    # Per-stack sections for the status page (uses the public-edge HTTP monitors,
    # falling back to internal where there is no public host).
    def http_ids(names, kind="https"):
        out = []
        for nm in names:
            for full, mid in NAME2ID.items():
                if full.startswith(f"{nm} :: {kind}"):
                    out.append(mid); break
        return out

    sections = [
        ("⚙️ Core Automation", http_ids(["n8n", "Evolution API", "TextBee"])),
        ("📣 Marketing", http_ids(["Postiz", "Listmonk", "Umami", "Matomo", "Metabase",
                                    "Typebot", "Chatwoot", "Plausible", "PostHog"])),
        ("🤖 AI Agents", http_ids(["Hermes", "Flowise", "Langflow", "LibreChat",
                                    "AnythingLLM", "Dify"])),
        ("📈 Observability", http_ids(["Grafana", "Uptime Kuma", "Dozzle", "Beszel"])),
        ("🗂️ Sites", http_ids(["Obsidian", "Uploads", "Downloads", "APK server",
                               "SillyTavern", "WebDAV"])),
        ("🗄️ Databases", ids_for(["Postgres", "Redis", "MongoDB", "MariaDB"])),
    ]
    build_status_page(sections)
finally:
    api.disconnect()
