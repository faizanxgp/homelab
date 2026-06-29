#!/usr/bin/env python3
"""Provision Uptime Kuma monitors for the whole homelab (idempotent)."""
import sys
from uptime_kuma_api import UptimeKumaApi, MonitorType

PW = sys.argv[1]
HTTP_CODES = ["200-299", "300-399", "400-499"]  # refused/timeout/5xx => DOWN
INTERVAL = 60

# (friendly name, type, kwargs)
PUBLIC = [  # full edge: DNS -> Cloudflare -> tunnel -> app
    ("n8n",        "https://n8n.itproxima.com/"),
    ("Evolution API", "https://evolution.itproxima.com/"),
    ("TextBee",    "https://text.itproxima.com/"),
    ("Homepage",   "https://home.itproxima.com/"),
    ("Dashy",      "https://dash.itproxima.com/"),
    ("Glance",     "https://glance.itproxima.com/"),
    ("Grafana",    "https://grafana.itproxima.com/"),
    ("Uptime Kuma","https://uptime.itproxima.com/"),
    ("Snippet Box","https://snippets.itproxima.com/"),
    ("SillyTavern","https://tavern.itproxima.com/"),
    ("APK server", "https://apk.itproxima.com/"),
    ("Downloads",  "https://downloads.itproxima.com/"),
    ("Uploads",    "https://uploads.itproxima.com/"),
    ("Obsidian",   "https://obsidian.itproxima.com/"),
    ("CouchDB",    "https://couch.itproxima.com/"),
    ("WebDAV",     "https://dav.itproxima.com/"),
]
INTERNAL = [  # app health by container name on the observatory network
    ("n8n (main)",      "http://n8n-main:5678/healthz"),
    ("Evolution API",   "http://evolution-api:8080/"),
    ("TextBee API",     "http://textbee-api:3001/"),
    ("TextBee Web",     "http://textbee-web:3000/"),
    ("Homepage",        "http://homepage:3000/"),
    ("Dashy",           "http://dashy:8080/"),
    ("Glance",          "http://glance:8080/"),
    ("Grafana",         "http://grafana:3000/api/health"),
    ("Snippet Box",     "http://snippetbox:5000/"),
    ("SillyTavern",     "http://sillytavern:8000/"),
    ("APK server",      "http://apk-server:80/"),
    ("Downloads",       "http://downloads:80/"),
    ("Uploads",         "http://uploads:80/"),
    ("Obsidian",        "http://obsidian:3000/"),
    ("CouchDB",         "http://couchdb:5984/"),
    ("WebDAV",          "http://webdav:6065/"),
    ("Prometheus",      "http://prometheus:9090/-/healthy"),
    ("Loki",            "http://loki:3100/ready"),
]
DBS = [  # TCP port checks (no creds stored)
    ("Postgres - n8n",          "n8n-postgres",        5432),
    ("Postgres - Evolution",    "evo-postgres",        5432),
    ("Postgres - automation",   "postgres-automation", 5432),
    ("Redis - n8n",             "n8n-redis",           6379),
    ("Redis - Evolution",       "evo-redis",           6379),
    ("Redis - TextBee",         "textbee-redis",       6379),
    ("MongoDB - TextBee",       "textbee-db",          27017),
]

api = UptimeKumaApi("http://127.0.0.1:3001")
api.login("faizanxgp", PW)

existing = {m["name"]: m for m in api.get_monitors()}

def ensure_group(name):
    if name in existing:
        return existing[name]["id"]
    r = api.add_monitor(type=MonitorType.GROUP, name=name)
    mid = r["monitorID"]
    existing[name] = {"id": mid, "name": name}
    print(f"  + group {name} (#{mid})")
    return mid

def ensure_http(name, url, parent):
    key = f"{name}"
    full = f"{key} :: {url}"
    if full in existing:
        return
    api.add_monitor(type=MonitorType.HTTP, name=full, url=url,
                    parent=parent, interval=INTERVAL,
                    accepted_statuscodes=HTTP_CODES, maxredirects=10)
    existing[full] = True
    print(f"    + {full}")

def ensure_port(name, host, port, parent):
    full = f"{name} :: {host}:{port}"
    if full in existing:
        return
    api.add_monitor(type=MonitorType.PORT, name=full, hostname=host,
                    port=port, parent=parent, interval=INTERVAL)
    existing[full] = True
    print(f"    + {full}")

try:
    g_pub = ensure_group("🌐 Public Sites")
    for n, u in PUBLIC:
        ensure_http(n, u, g_pub)
    g_int = ensure_group("🧩 Internal Apps")
    for n, u in INTERNAL:
        ensure_http(n, u, g_int)
    g_db = ensure_group("🗄️ Databases")
    for n, h, p in DBS:
        ensure_port(n, h, p, g_db)
    print("TOTAL monitors now:", len(api.get_monitors()))
finally:
    api.disconnect()
