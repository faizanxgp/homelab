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
    ("Postiz",     "https://postiz.itproxima.com/"),
    ("Hermes",     "https://hermes.itproxima.com/"),
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
    ("Postiz",          "http://postiz:5000/"),
    ("Hermes",          "http://hermes:8080/"),
]
DBS = [  # TCP port checks (no creds stored)
    ("Postgres - n8n",          "n8n-postgres",        5432),
    ("Postgres - Evolution",    "evo-postgres",        5432),
    ("Postgres - automation",   "automation-postgres", 5432),
    ("Redis - n8n",             "n8n-redis",           6379),
    ("Redis - Evolution",       "evo-redis",           6379),
    ("Redis - TextBee",         "textbee-redis",       6379),
    ("MongoDB - TextBee",       "textbee-db",          27017),
]
# Endpoint-less services: no HTTP/TCP health to hit, so monitor the Docker
# container's running-state directly via the mounted /var/run/docker.sock.
CONTAINERS = [
    "promtail", "cloudflared", "node-exporter", "cadvisor",
    "couchdb-exporter",
    "n8n-postgres-exporter", "n8n-redis-exporter",
    "evo-postgres-exporter", "evo-redis-exporter",
    "automation-postgres-exporter",
    "textbee-mongo-exporter", "textbee-redis-exporter",
    # Postiz stack (no public endpoints — watch container state)
    "postiz-postgres", "postiz-redis",
    "temporal", "temporal-postgresql", "temporal-elasticsearch",
]
DOCKER_HOST_NAME = "local-socket"
DOCKER_SOCK = "/var/run/docker.sock"

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

def ensure_docker_host():
    for h in api.get_docker_hosts():
        if h.get("name") == DOCKER_HOST_NAME:
            return h["id"]
    r = api.add_docker_host(name=DOCKER_HOST_NAME, dockerType="socket",
                            dockerDaemon=DOCKER_SOCK)
    hid = (r or {}).get("id") or (r or {}).get("dockerHostID")
    if hid is None:  # fall back to re-reading the list
        for h in api.get_docker_hosts():
            if h.get("name") == DOCKER_HOST_NAME:
                hid = h["id"]; break
    print(f"  + docker host {DOCKER_HOST_NAME} (#{hid})")
    return hid

def ensure_docker(container, host_id, parent):
    full = f"{container} :: container"
    if full in existing:
        return
    api.add_monitor(type=MonitorType.DOCKER, name=full, parent=parent,
                    interval=INTERVAL, docker_container=container,
                    docker_host=host_id)
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
    g_ctr = ensure_group("🐳 Containers (no endpoint)")
    host_id = ensure_docker_host()
    for c in CONTAINERS:
        ensure_docker(c, host_id, g_ctr)
    print("TOTAL monitors now:", len(api.get_monitors()))
finally:
    api.disconnect()
